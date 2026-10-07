from oacg.compare import compare_specs


def spec(operation, path="/accounts", version="3.0.3"):
    return {"openapi": version, "info": {"title": "Accounts", "version": "1"}, "paths": {path: operation}}


def get_op(**kwargs):
    base = {"responses": {"200": {"description": "OK", "content": {"application/json": {"schema": {"type": "object", "properties": {"id": {"type": "string"}}}}}}}}
    base.update(kwargs)
    return {"get": base}


def ids(report):
    return {finding.rule_id for finding in report.findings}


def test_identical_specs_are_compatible():
    document = spec(get_op())
    report = compare_specs(document, document)
    assert report.compatible
    assert report.findings == ()


def test_removed_path_is_breaking():
    report = compare_specs(spec(get_op()), {"openapi": "3.0.3", "paths": {}})
    assert "PATH_REMOVED" in ids(report)
    assert not report.compatible


def test_removed_operation_is_breaking():
    report = compare_specs(spec(get_op()), spec({}))
    assert "OPERATION_REMOVED" in ids(report)


def test_required_parameter_addition_is_breaking():
    old = get_op()
    new = get_op(parameters=[{"name": "tenant", "in": "query", "required": True, "schema": {"type": "string"}}])
    report = compare_specs(spec(old), spec(new))
    assert "PARAMETER_ADDED_REQUIRED" in ids(report)


def test_optional_parameter_becoming_required_is_breaking():
    old = get_op(parameters=[{"name": "page", "in": "query", "required": False, "schema": {"type": "integer"}}])
    new = get_op(parameters=[{"name": "page", "in": "query", "required": True, "schema": {"type": "integer"}}])
    assert "PARAMETER_NOW_REQUIRED" in ids(compare_specs(spec(old), spec(new)))


def test_response_removed_is_breaking():
    old = get_op()
    new = get_op(responses={"201": {"description": "Created"}})
    assert "RESPONSE_REMOVED" in ids(compare_specs(spec(old), spec(new)))


def test_schema_type_change_is_breaking():
    old = get_op()
    new = get_op(responses={"200": {"description": "OK", "content": {"application/json": {"schema": {"type": "integer"}}}}})
    assert "SCHEMA_TYPE_CHANGED" in ids(compare_specs(spec(old), spec(new)))


def test_required_field_addition_is_breaking():
    old = get_op(responses={"200": {"description": "OK", "content": {"application/json": {"schema": {"type": "object", "properties": {"id": {"type": "string"}}}}}}})
    new = get_op(responses={"200": {"description": "OK", "content": {"application/json": {"schema": {"type": "object", "required": ["id", "name"], "properties": {"id": {"type": "string"}, "name": {"type": "string"}}}}}}})
    assert "FIELD_NOW_REQUIRED" in ids(compare_specs(spec(old), spec(new)))


def test_enum_narrowing_is_breaking():
    old = get_op(responses={"200": {"description": "OK", "content": {"application/json": {"schema": {"type": "string", "enum": ["ACTIVE", "PENDING"]}}}}})
    new = get_op(responses={"200": {"description": "OK", "content": {"application/json": {"schema": {"type": "string", "enum": ["ACTIVE"]}}}}})
    assert "ENUM_VALUES_REMOVED" in ids(compare_specs(spec(old), spec(new)))


def test_local_schema_ref_is_resolved():
    old = spec(get_op(responses={"200": {"description": "OK", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Account"}}}}}))
    new = spec(get_op(responses={"200": {"description": "OK", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Account"}}}}}))
    old["components"] = {"schemas": {"Account": {"type": "object", "properties": {"balance": {"type": "number"}}}}}
    new["components"] = {"schemas": {"Account": {"type": "object", "properties": {"balance": {"type": "string"}}}}}
    assert "SCHEMA_TYPE_CHANGED" in ids(compare_specs(old, new))


def test_findings_are_deterministic():
    old = {"openapi": "3.0.3", "paths": {"/z": {"get": {"responses": {}}}, "/a": {"get": {"responses": {}}}}}
    new = {"openapi": "3.0.3", "paths": {}}
    first = compare_specs(old, new).to_dict()
    second = compare_specs(old, new).to_dict()
    assert first == second


def test_parameter_removal_is_breaking():
    old = get_op(parameters=[{"name": "page", "in": "query", "schema": {"type": "integer"}}])
    assert "PARAMETER_REMOVED" in ids(compare_specs(spec(old), spec(get_op())))


def test_optional_parameter_addition_is_compatible():
    new = get_op(parameters=[{"name": "page", "in": "query", "required": False, "schema": {"type": "integer"}}])
    report = compare_specs(spec(get_op()), spec(new))
    assert report.compatible


def test_required_request_body_addition_is_breaking():
    body = {"required": True, "content": {"application/json": {"schema": {"type": "object"}}}}
    assert "REQUEST_BODY_ADDED_REQUIRED" in ids(compare_specs(spec({"post": {"responses": {}}}), spec({"post": {"requestBody": body, "responses": {}}})))


def test_request_body_removal_is_breaking():
    body = {"content": {"application/json": {"schema": {"type": "object"}}}}
    old = {"post": {"requestBody": body, "responses": {}}}
    new = {"post": {"responses": {}}}
    assert "REQUEST_BODY_REMOVED" in ids(compare_specs(spec(old), spec(new)))


def test_request_body_becoming_required_and_media_type_removed():
    old_body = {"required": False, "content": {"application/json": {"schema": {"type": "object"}}, "text/plain": {"schema": {"type": "string"}}}}
    new_body = {"required": True, "content": {"application/json": {"schema": {"type": "string"}}}}
    old = {"post": {"requestBody": old_body, "responses": {}}}
    new = {"post": {"requestBody": new_body, "responses": {}}}
    found = ids(compare_specs(spec(old), spec(new)))
    assert {"REQUEST_BODY_NOW_REQUIRED", "REQUEST_MEDIA_TYPE_REMOVED", "SCHEMA_TYPE_CHANGED"} <= found


def test_response_media_type_removal_and_array_item_change():
    old_schema = {"type": "array", "items": {"type": "integer"}}
    new_schema = {"type": "array", "items": {"type": "string"}}
    old = get_op(responses={"200": {"description": "OK", "content": {"application/json": {"schema": old_schema}, "text/plain": {"schema": {"type": "string"}}}}})
    new = get_op(responses={"200": {"description": "OK", "content": {"application/json": {"schema": new_schema}}}})
    found = ids(compare_specs(spec(old), spec(new)))
    assert {"RESPONSE_MEDIA_TYPE_REMOVED", "SCHEMA_TYPE_CHANGED"} <= found


def test_removed_property_and_restricted_additional_properties_are_warnings():
    old_schema = {"type": "object", "properties": {"id": {"type": "string"}, "label": {"type": "string"}}}
    new_schema = {"type": "object", "additionalProperties": False, "properties": {"id": {"type": "string"}}}
    old = get_op(responses={"200": {"description": "OK", "content": {"application/json": {"schema": old_schema}}}})
    new = get_op(responses={"200": {"description": "OK", "content": {"application/json": {"schema": new_schema}}}})
    report = compare_specs(spec(old), spec(new))
    assert {finding.rule_id for finding in report.findings} == {"PROPERTY_REMOVED", "ADDITIONAL_PROPERTIES_DISABLED"}
    assert report.warning_count == 2
    assert report.compatible


def test_external_and_missing_local_refs_are_not_fetched():
    external = {"$ref": "https://example.invalid/schemas/Account"}
    missing = {"$ref": "#/components/schemas/Missing"}
    old = get_op(responses={"200": {"description": "OK", "content": {"application/json": {"schema": external}}}})
    new = get_op(responses={"200": {"description": "OK", "content": {"application/json": {"schema": missing}}}})
    assert compare_specs(spec(old), spec(new)).findings == ()


def test_ref_siblings_are_merged_for_openapi_31():
    old = spec(get_op(responses={"200": {"description": "OK", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Account", "type": "string"}}}}}), version="3.1.0")
    new = spec(get_op(responses={"200": {"description": "OK", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Account", "type": "integer"}}}}}), version="3.1.0")
    old["components"] = new["components"] = {"schemas": {"Account": {"type": "object"}}}
    assert "SCHEMA_TYPE_CHANGED" in ids(compare_specs(old, new))


def test_invalid_paths_mapping_returns_finding():
    report = compare_specs({"openapi": "3.0.3", "paths": []}, {"openapi": "3.0.3", "paths": {}})
    assert "INVALID_PATHS" in ids(report)


def test_non_mapping_path_item_is_ignored():
    report = compare_specs({"openapi": "3.0.3", "paths": {"/x": "invalid"}}, {"openapi": "3.0.3", "paths": {"/x": {}}})
    assert report.findings == ()


def test_ref_siblings_are_ignored_for_openapi_30():
    old = spec(get_op(responses={"200": {"description": "OK", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Account", "type": "string"}}}}}), version="3.0.3")
    new = spec(get_op(responses={"200": {"description": "OK", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Account", "type": "integer"}}}}}), version="3.0.3")
    old["components"] = new["components"] = {"schemas": {"Account": {"type": "object"}}}
    assert compare_specs(old, new).findings == ()


def test_path_level_parameter_removal_is_breaking():
    old = {"/accounts": {"parameters": [{"name": "tenant", "in": "header", "required": True, "schema": {"type": "string"}}], **get_op()}}
    new = {"/accounts": get_op()}
    assert "PARAMETER_REMOVED" in ids(compare_specs({"openapi": "3.0.3", "paths": old}, {"openapi": "3.0.3", "paths": new}))


def test_operation_parameter_overrides_path_parameter():
    old = {"/accounts": {"parameters": [{"name": "tenant", "in": "header", "required": False, "schema": {"type": "string"}}], **get_op()}}
    new = {"/accounts": {"parameters": [{"name": "tenant", "in": "header", "required": False, "schema": {"type": "string"}}], "get": {**get_op()["get"], "parameters": [{"name": "tenant", "in": "header", "required": True, "schema": {"type": "string"}}]}}}
    assert "PARAMETER_NOW_REQUIRED" in ids(compare_specs({"openapi": "3.0.3", "paths": old}, {"openapi": "3.0.3", "paths": new}))


def test_required_request_body_reference_addition_is_breaking():
    baseline = {
        "openapi": "3.0.3",
        "paths": {"/x": {"post": {"responses": {}}}},
    }
    candidate = {
        "openapi": "3.0.3",
        "paths": {
            "/x": {
                "post": {
                    "requestBody": {"$ref": "#/components/requestBodies/Create"},
                    "responses": {},
                }
            }
        },
        "components": {
            "requestBodies": {
                "Create": {
                    "required": True,
                    "content": {"application/json": {"schema": {"type": "object"}}},
                }
            }
        },
    }
    assert "REQUEST_BODY_ADDED_REQUIRED" in ids(compare_specs(baseline, candidate))
