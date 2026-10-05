# Data Contract Validator

A production-oriented batch data-quality gate for data pipelines. It validates CSV datasets against versioned YAML contracts, produces machine-readable quality reports, and returns deterministic exit codes suitable for CI/CD and orchestration systems.

## Why this exists

Data pipelines often fail downstream because schema changes, unexpected nulls, duplicate identifiers, malformed values, or domain violations are discovered too late. This service moves those failures to an explicit quality boundary.

## Capabilities

- Declarative YAML data contracts
- Schema and unknown-column enforcement
- Type validation for strings, integers, numbers, booleans, and emails
- Null-ratio constraints
- Uniqueness constraints
- Allowed-value/domain constraints
- Dataset profiling
- Atomic JSON report generation
- CI-friendly exit codes
- Docker image
- Unit tests and CI smoke test

## Usage

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e . -r requirements-dev.txt
pytest -q
dcv examples/customers.csv --contract examples/customers.contract.yaml --report build/report.json
```

Exit codes:
- `0`: quality gate passed
- `2`: data contract failed
- `1`: operational/configuration error

## Engineering decisions

The validation engine is separated from the CLI so it can be embedded in an orchestrator later. Reports are JSON rather than human-only text so they can be consumed by CI, observability systems, or a data platform. Dependencies are deliberately small because the problem does not require a web framework or database.

## Production evolution

For large datasets, the next scaling step is chunked/streaming validation with bounded memory. In an enterprise platform, contracts could be stored and versioned centrally, reports written to object storage, and validation jobs executed by an orchestrator such as Kubernetes, Airflow, or Dagster.
