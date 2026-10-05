# Architecture

The validator is a batch data-quality gate. A CLI loads a declarative YAML contract, streams a CSV into memory for deterministic validation, executes schema/type/null/uniqueness/domain checks, profiles the dataset, and atomically writes a JSON report.

The core is framework-light so it can later be embedded into Airflow, Dagster, Kubernetes Jobs, or CI pipelines without coupling the validation rules to an orchestration platform.

The report is intentionally machine-readable. Exit code `0` means the quality gate passed, `2` means contract validation failed, and `1` means an operational/configuration error.
