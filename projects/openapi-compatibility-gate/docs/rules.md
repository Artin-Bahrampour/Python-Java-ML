# Compatibility rule catalogue

OACG emits stable rule IDs so teams can review findings, build dashboards, and later add organization-specific policy.

| Rule ID | Default severity | Trigger | Rationale |
|---|---|---|---|
| `PATH_REMOVED` | Breaking | A baseline path is absent from the candidate | Existing clients cannot call the endpoint. |
| `OPERATION_REMOVED` | Breaking | A baseline HTTP method is absent from a retained path | A previously supported operation disappears. |
| `PARAMETER_REMOVED` | Breaking | A path- or operation-level parameter is removed | Requests using the prior contract may no longer be representable. |
| `PARAMETER_ADDED_REQUIRED` | Breaking | A newly introduced parameter is required (including path parameters) | Existing callers do not supply it. |
| `PARAMETER_NOW_REQUIRED` | Breaking | An optional parameter becomes required | Existing requests may be rejected. |
| `REQUEST_BODY_ADDED_REQUIRED` | Breaking | A required request body is introduced | Existing callers may not send a body. |
| `REQUEST_BODY_REMOVED` | Breaking | A prior request body is removed | Previously valid requests may no longer be accepted. |
| `REQUEST_BODY_NOW_REQUIRED` | Breaking | An optional request body becomes required | Body-less requests may be rejected. |
| `REQUEST_MEDIA_TYPE_REMOVED` | Breaking | A previously supported request media type disappears | Clients using that representation cannot submit the request. |
| `RESPONSE_REMOVED` | Breaking | A prior response status is removed | Clients may rely on that status or its documented payload. |
| `RESPONSE_MEDIA_TYPE_REMOVED` | Breaking | A response media type disappears | Clients negotiating that representation may fail. |
| `SCHEMA_TYPE_CHANGED` | Breaking | A common schema node changes declared type | Generated clients and validators may no longer agree with payload shape. |
| `ENUM_VALUES_REMOVED` | Breaking | A declared enum loses previously accepted values | Clients sending or handling removed values can fail. |
| `FIELD_NOW_REQUIRED` | Breaking | A schema property becomes required | The contract becomes stricter; direction-specific policy may refine this rule. |
| `PROPERTY_REMOVED` | Warning | A schema property disappears | Impact depends on request/response direction and client behavior. |
| `ADDITIONAL_PROPERTIES_DISABLED` | Warning | `additionalProperties` becomes `false` | Previously tolerated extension fields may be rejected. |

Severity is deliberately conservative and should be treated as a release signal, not a substitute for contract review. The comparator resolves local JSON Pointer references only. External references are not fetched.
