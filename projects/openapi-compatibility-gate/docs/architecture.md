# Architecture

## Execution model

OACG is a deterministic, offline CLI. It reads a baseline contract and a candidate contract, performs structural compatibility checks, emits human-readable findings, and optionally writes a machine-readable JSON report. It does not call the API or access the network.

## Components

- `spec_loader`: bounded file reads, UTF-8 decoding, safe YAML parsing, JSON parsing, and basic OpenAPI version/root checks.
- `compare`: semantic rules for removed paths/operations/responses, parameter changes, request-body changes, and common schema changes. Local JSON Pointer `$ref` references are resolved for comparison.
- `models`: immutable finding/report models and stable JSON shape.
- `report`: atomic replacement of report files to avoid partially written CI artifacts.
- `cli`: exit-code contract for automation.

## Exit codes

- `0`: no breaking findings (or warnings when `--fail-on-warning` is not set).
- `1`: breaking changes found, or warnings found with `--fail-on-warning`.
- `2`: input parsing, structural validation, or report-writing failure.

## Design trade-offs

The tool implements a documented subset of OpenAPI compatibility semantics rather than attempting to be a full OpenAPI validator. It does not dereference remote references, execute vendor extensions, or fetch URLs. External `$ref` values are deliberately left unresolved. Findings are sorted for reproducible CI output. The current schema comparator is conservative: a removed property is a warning because compatibility depends on whether the schema is used for requests or responses.

## Extension points

New rules should be implemented as small comparison functions with stable rule IDs and direct tests. Rule severity and whether a change is breaking should be documented, because teams use exit codes as release gates.
