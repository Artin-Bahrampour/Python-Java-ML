"""Safe loading and minimal structural validation for OpenAPI documents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .errors import SpecLoadError, SpecValidationError

MAX_SPEC_BYTES = 5 * 1024 * 1024
SUPPORTED_OPENAPI_PREFIXES = ("3.0.", "3.1.")


def load_spec(path: str | Path) -> dict[str, Any]:
    """Load JSON or YAML without permitting arbitrary YAML object construction."""
    source = Path(path)
    try:
        raw = source.read_bytes()
    except OSError as exc:
        raise SpecLoadError(f"Cannot read specification '{source}': {exc.strerror or exc}") from exc

    if not raw:
        raise SpecLoadError(f"Specification '{source}' is empty")
    if len(raw) > MAX_SPEC_BYTES:
        raise SpecLoadError(
            f"Specification '{source}' exceeds the {MAX_SPEC_BYTES // (1024 * 1024)} MiB size limit"
        )

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SpecLoadError(f"Specification '{source}' is not valid UTF-8") from exc

    try:
        if source.suffix.lower() == ".json":
            document = json.loads(text)
        else:
            document = yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise SpecLoadError(f"Cannot parse specification '{source}': {exc}") from exc

    if not isinstance(document, dict):
        raise SpecValidationError("OpenAPI document root must be an object")

    version = document.get("openapi")
    if not isinstance(version, str) or not version.startswith(SUPPORTED_OPENAPI_PREFIXES):
        raise SpecValidationError("Only OpenAPI 3.0.x and 3.1.x documents are supported")
    if not isinstance(document.get("paths", {}), dict):
        raise SpecValidationError("The 'paths' field must be an object when present")
    if "components" in document and not isinstance(document["components"], dict):
        raise SpecValidationError("The 'components' field must be an object when present")
    return document
