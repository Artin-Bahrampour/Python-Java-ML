"""Semantic comparison rules for common OpenAPI compatibility changes.

The analyzer intentionally implements a documented subset of OpenAPI semantics.
It fails closed for known breaking changes and avoids claiming full spec validation.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .models import ComparisonReport, Finding

HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}


def _pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _resolve_local_ref(document: Mapping[str, Any], value: Any, seen: frozenset[str] = frozenset()) -> Any:
    """Resolve local JSON Pointer refs; leave external refs unresolved by design."""
    if not isinstance(value, Mapping) or "$ref" not in value:
        return value
    ref = value.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#/") or ref in seen:
        return value
    current: Any = document
    try:
        for token in ref[2:].split("/"):
            token = token.replace("~1", "/").replace("~0", "~")
            current = current[token]
    except (KeyError, TypeError):
        return value
    return _resolve_local_ref(document, current, seen | {ref})


def _effective(value: Any, document: Mapping[str, Any]) -> Any:
    resolved = _resolve_local_ref(document, value)
    if isinstance(resolved, Mapping) and isinstance(value, Mapping):
        # OpenAPI 3.1 permits schema siblings alongside $ref. In 3.0, a Reference
        # Object's extra fields are ignored, so do not accidentally treat them as overrides.
        siblings = {key: item for key, item in value.items() if key != "$ref"}
        is_openapi_31 = str(document.get("openapi", "")).startswith("3.1.")
        if siblings and is_openapi_31:
            merged = dict(resolved)
            merged.update(siblings)
            return merged
    return resolved


def _schema_findings(
    before: Any,
    after: Any,
    document_before: Mapping[str, Any],
    document_after: Mapping[str, Any],
    location: str,
) -> list[Finding]:
    old = _effective(before, document_before)
    new = _effective(after, document_after)
    if not isinstance(old, Mapping) or not isinstance(new, Mapping):
        return []

    findings: list[Finding] = []
    old_type, new_type = old.get("type"), new.get("type")
    if old_type is not None and new_type is not None and old_type != new_type:
        findings.append(Finding("SCHEMA_TYPE_CHANGED", "breaking", location, "Schema type changed.", old_type, new_type))

    old_enum, new_enum = old.get("enum"), new.get("enum")
    if isinstance(old_enum, list) and isinstance(new_enum, list):
        removed = [value for value in old_enum if value not in new_enum]
        if removed:
            findings.append(Finding("ENUM_VALUES_REMOVED", "breaking", location, "Previously accepted enum values were removed.", removed, new_enum))

    old_required = set(old.get("required", [])) if isinstance(old.get("required", []), list) else set()
    new_required = set(new.get("required", [])) if isinstance(new.get("required", []), list) else set()
    for field in sorted(new_required - old_required):
        findings.append(Finding("FIELD_NOW_REQUIRED", "breaking", f"{location}/required/{_pointer_escape(str(field))}", "A previously optional property is now required.", False, True))

    old_properties = old.get("properties", {})
    new_properties = new.get("properties", {})
    if isinstance(old_properties, Mapping) and isinstance(new_properties, Mapping):
        for name in sorted(old_properties.keys() & new_properties.keys(), key=str):
            findings.extend(
                _schema_findings(
                    old_properties[name], new_properties[name], document_before, document_after,
                    f"{location}/properties/{_pointer_escape(str(name))}",
                )
            )
        # Removing a response property can break consumers. For request schemas it can be permissive,
        # but the comparison engine does not yet infer direction at schema recursion level.
        for name in sorted(old_properties.keys() - new_properties.keys(), key=str):
            findings.append(Finding("PROPERTY_REMOVED", "warning", f"{location}/properties/{_pointer_escape(str(name))}", "A schema property was removed; review consumer compatibility."))

    old_items, new_items = old.get("items"), new.get("items")
    if old_items is not None and new_items is not None:
        findings.extend(_schema_findings(old_items, new_items, document_before, document_after, f"{location}/items"))

    old_additional, new_additional = old.get("additionalProperties"), new.get("additionalProperties")
    if old_additional is not False and new_additional is False:
        findings.append(Finding("ADDITIONAL_PROPERTIES_DISABLED", "warning", location, "The schema now rejects additional properties."))

    return findings


def _parameters(
    operation: Mapping[str, Any], document: Mapping[str, Any], inherited: Any = None
) -> dict[tuple[str, str], Mapping[str, Any]]:
    """Merge path-level parameters with operation-level overrides."""
    result: dict[tuple[str, str], Mapping[str, Any]] = {}
    inherited_parameters = inherited if isinstance(inherited, list) else []
    operation_parameters = operation.get("parameters", [])
    if not isinstance(operation_parameters, list):
        operation_parameters = []
    for raw in [*inherited_parameters, *operation_parameters]:
        parameter = _effective(raw, document)
        if not isinstance(parameter, Mapping):
            continue
        name, location = parameter.get("name"), parameter.get("in")
        if isinstance(name, str) and isinstance(location, str):
            result[(location, name)] = parameter
    return result


def compare_specs(
    baseline: Mapping[str, Any], candidate: Mapping[str, Any], baseline_name: str = "baseline", candidate_name: str = "candidate"
) -> ComparisonReport:
    findings: list[Finding] = []
    old_paths = baseline.get("paths", {})
    new_paths = candidate.get("paths", {})
    if not isinstance(old_paths, Mapping) or not isinstance(new_paths, Mapping):
        return ComparisonReport(baseline_name, candidate_name, (Finding("INVALID_PATHS", "breaking", "/paths", "Paths must be objects."),))

    for path in sorted(old_paths.keys() - new_paths.keys(), key=str):
        findings.append(Finding("PATH_REMOVED", "breaking", f"/paths/{_pointer_escape(str(path))}", "An existing endpoint path was removed."))

    for path in sorted(old_paths.keys() & new_paths.keys(), key=str):
        old_item, new_item = old_paths[path], new_paths[path]
        if not isinstance(old_item, Mapping) or not isinstance(new_item, Mapping):
            continue
        for method in sorted((key.lower() for key in old_item.keys() if str(key).lower() in HTTP_METHODS)):
            old_op = old_item.get(method, old_item.get(method.upper()))
            new_op = new_item.get(method, new_item.get(method.upper()))
            base_location = f"/paths/{_pointer_escape(str(path))}/{method}"
            if not isinstance(new_op, Mapping):
                findings.append(Finding("OPERATION_REMOVED", "breaking", base_location, "An existing HTTP operation was removed."))
                continue
            if not isinstance(old_op, Mapping):
                continue

            old_params = _parameters(old_op, baseline, old_item.get("parameters", []))
            new_params = _parameters(new_op, candidate, new_item.get("parameters", []))
            for key in sorted(old_params.keys() - new_params.keys()):
                findings.append(Finding("PARAMETER_REMOVED", "breaking", f"{base_location}/parameters/{key[0]}:{key[1]}", "An existing parameter was removed."))
            for key in sorted(new_params.keys() - old_params.keys()):
                param = new_params[key]
                if param.get("required") is True or (key[0] == "path" and param.get("required") is not False):
                    findings.append(Finding("PARAMETER_ADDED_REQUIRED", "breaking", f"{base_location}/parameters/{key[0]}:{key[1]}", "A required parameter was added."))
            for key in sorted(old_params.keys() & new_params.keys()):
                old_param, new_param = old_params[key], new_params[key]
                if old_param.get("required") is not True and new_param.get("required") is True:
                    findings.append(Finding("PARAMETER_NOW_REQUIRED", "breaking", f"{base_location}/parameters/{key[0]}:{key[1]}", "An optional parameter is now required."))
                findings.extend(_schema_findings(old_param.get("schema", {}), new_param.get("schema", {}), baseline, candidate, f"{base_location}/parameters/{key[0]}:{key[1]}/schema"))

            old_body = old_op.get("requestBody")
            new_body = new_op.get("requestBody")
            new_body_effective = _effective(new_body, candidate) if new_body is not None else None
            if old_body is None and isinstance(new_body_effective, Mapping) and new_body_effective.get("required") is True:
                findings.append(Finding("REQUEST_BODY_ADDED_REQUIRED", "breaking", f"{base_location}/requestBody", "A required request body was added."))
            elif old_body is not None and new_body is None:
                findings.append(Finding("REQUEST_BODY_REMOVED", "breaking", f"{base_location}/requestBody", "An existing request body was removed."))
            elif old_body is not None and new_body is not None:
                old_body_eff, new_body_eff = _effective(old_body, baseline), _effective(new_body, candidate)
                if isinstance(old_body_eff, Mapping) and isinstance(new_body_eff, Mapping):
                    if old_body_eff.get("required") is not True and new_body_eff.get("required") is True:
                        findings.append(Finding("REQUEST_BODY_NOW_REQUIRED", "breaking", f"{base_location}/requestBody", "The request body is now required."))
                    old_content = old_body_eff.get("content", {})
                    new_content = new_body_eff.get("content", {})
                    if isinstance(old_content, Mapping) and isinstance(new_content, Mapping):
                        for media in sorted(old_content.keys() - new_content.keys(), key=str):
                            findings.append(Finding("REQUEST_MEDIA_TYPE_REMOVED", "breaking", f"{base_location}/requestBody/content/{_pointer_escape(str(media))}", "A request media type was removed."))
                        for media in sorted(old_content.keys() & new_content.keys(), key=str):
                            old_media, new_media = old_content[media], new_content[media]
                            if isinstance(old_media, Mapping) and isinstance(new_media, Mapping):
                                findings.extend(_schema_findings(old_media.get("schema", {}), new_media.get("schema", {}), baseline, candidate, f"{base_location}/requestBody/content/{_pointer_escape(str(media))}/schema"))

            old_responses = old_op.get("responses", {})
            new_responses = new_op.get("responses", {})
            if isinstance(old_responses, Mapping) and isinstance(new_responses, Mapping):
                for code in sorted(old_responses.keys() - new_responses.keys(), key=str):
                    findings.append(Finding("RESPONSE_REMOVED", "breaking", f"{base_location}/responses/{code}", "An existing response status was removed."))
                for code in sorted(old_responses.keys() & new_responses.keys(), key=str):
                    old_response = _effective(old_responses[code], baseline)
                    new_response = _effective(new_responses[code], candidate)
                    if not isinstance(old_response, Mapping) or not isinstance(new_response, Mapping):
                        continue
                    old_content, new_content = old_response.get("content", {}), new_response.get("content", {})
                    if isinstance(old_content, Mapping) and isinstance(new_content, Mapping):
                        for media in sorted(old_content.keys() - new_content.keys(), key=str):
                            findings.append(Finding("RESPONSE_MEDIA_TYPE_REMOVED", "breaking", f"{base_location}/responses/{code}/content/{_pointer_escape(str(media))}", "A response media type was removed."))
                        for media in sorted(old_content.keys() & new_content.keys(), key=str):
                            old_media, new_media = old_content[media], new_content[media]
                            if isinstance(old_media, Mapping) and isinstance(new_media, Mapping):
                                findings.extend(_schema_findings(old_media.get("schema", {}), new_media.get("schema", {}), baseline, candidate, f"{base_location}/responses/{code}/content/{_pointer_escape(str(media))}/schema"))

    # Stable ordering makes CI output and generated reports reproducible.
    findings.sort(key=lambda item: (item.severity, item.location, item.rule_id, item.message))
    return ComparisonReport(baseline_name, candidate_name, tuple(findings))
