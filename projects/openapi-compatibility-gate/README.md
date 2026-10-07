# OpenAPI Compatibility Gate (OACG)

A CI-friendly compatibility gate for API teams. OACG compares a released OpenAPI contract with a proposed revision and identifies likely breaking changes before they reach consumers.

## Why it exists

An API can compile and pass its own tests while still breaking downstream clients: a response disappears, a parameter becomes mandatory, an enum value is removed, or a response field changes type. OACG turns a baseline-versus-candidate contract review into a repeatable release check with deterministic findings and machine-readable output.

## Capabilities

- Supports OpenAPI 3.0.x and 3.1.x documents in YAML or JSON.
- Detects removed paths, operations, response codes, response media types, request media types, and parameters.
- Detects newly required parameters and request bodies.
- Compares common schema changes: type changes, enum narrowing, newly required properties, removed properties (warning), and stricter `additionalProperties` behavior (warning).
- Resolves local JSON Pointer `$ref` references; never fetches external references.
- Produces stable text output and an optional JSON report.
- Provides CI-safe exit codes and a `--fail-on-warning` mode.
- Includes unit tests, coverage threshold, Docker packaging, examples, and GitHub Actions CI.

## Requirements

- Python 3.11 or newer
- pip

## Install

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
```

On Windows, activate the virtual environment with `.venv\\Scripts\\activate`.

## Quick start

Compatible candidate (exit code `0`):

```bash
oacg examples/baseline.yaml examples/candidate-compatible.yaml --report build/compatibility.json
```

Breaking candidate (exit code `1`, expected for this example):

```bash
oacg examples/baseline.yaml examples/candidate-breaking.yaml --report build/breaking.json
```

Input/parse errors return exit code `2`.

## Example finding

```text
[BREAKING] RESPONSE_REMOVED /paths/~1accounts~1{accountId}/get/responses/404: An existing response status was removed.
[BREAKING] FIELD_NOW_REQUIRED /paths/~1accounts~1{accountId}/get/responses/200/content/application~1json/schema/required/displayName: A previously optional property is now required.
[BREAKING] ENUM_VALUES_REMOVED /paths/~1accounts~1{accountId}/get/responses/200/content/application~1json/schema/properties/status: Previously accepted enum values were removed.
BREAKING CHANGES FOUND: 3 breaking, 0 warning(s), 3 total finding(s)
```

Exact finding counts depend on the comparison rules and spec content.

## JSON report

The report includes a versioned top-level schema, compatibility summary, and a sorted list of findings. Each finding contains a stable `rule_id`, severity, JSON-Pointer-like location, and concise explanation. This is intended for CI artifacts and later integration into release tooling.

## CI integration

Example GitHub Actions step:

```yaml
- name: Check API compatibility
  run: |
    oacg api/openapi-released.yaml api/openapi.yaml --report build/api-compatibility.json
```

The command exits non-zero when breaking changes are found. Keep the released contract versioned alongside the service or fetch it from a trusted artifact store in your own pipeline.

## Docker

```bash
docker build -t oacg:local .
docker run --rm -v "$PWD/examples:/specs:ro" oacg:local /specs/baseline.yaml /specs/candidate-compatible.yaml
```

## Test and coverage

```bash
coverage run -m pytest
coverage report
```

The configured coverage threshold is 85% branch-aware coverage. CI tests Python 3.11 and 3.12 and runs compatible/breaking CLI smoke tests.

## Compatibility policy and limitations

OACG is a compatibility analyzer, not a complete OpenAPI validator. It implements a conservative, documented subset of common breaking-change rules. In particular:

- External `$ref` values are not fetched or resolved.
- Security-scheme changes, server URL changes, discriminator behavior, complex `oneOf`/`anyOf` subsumption, and every OpenAPI edge case are not currently analyzed.
- A removed property is reported as a warning because impact depends on request-versus-response direction and consumer behavior.
- Schema compatibility is not inferred from examples or vendor extensions.

Run a standards-compliant OpenAPI validator separately and review warnings with API owners. See [Architecture](docs/architecture.md), [Rule Catalogue](docs/rules.md), and [Threat Model](docs/threat-model.md).

## Project structure

```text
src/oacg/       loader, comparison engine, report models, atomic writer, CLI
 tests/         unit and CLI tests
 examples/      baseline and compatible/breaking candidate specifications
 docs/          architecture and threat model
 .github/       CI workflow
```

## License

MIT. See [LICENSE](LICENSE).
