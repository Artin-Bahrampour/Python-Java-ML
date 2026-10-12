# SQL Lineage & Impact Analyzer

A command-line engineering tool that reconstructs dependencies between SQL transformation models and explains which downstream models are affected by a change. It is designed for analytics-engineering and data-platform repositories where a small SQL change can silently invalidate multiple downstream datasets.

This is a portfolio-quality static-analysis tool. It **parses SQL but never executes it**, connects to no database, and requires no credentials.

## Business problem

Data teams need to understand the blast radius of a transformation change before merging it. Without an explicit lineage graph, reviewers must manually search SQL files, infer dependencies through CTEs and joins, and hope they have not missed a downstream model. That process is slow and error-prone.

The analyzer provides a deterministic inventory of model dependencies, external source tables, dependency edges, cycles, a dependency-safe build order, and a transitive downstream impact report. It can be used locally or as a CI gate.

## Capabilities

- Parses PostgreSQL-oriented SQL with SQLGlot, including CTEs, joins, quoted identifiers, and nested queries.
- Treats each `.sql` file as one model; the filename stem is the model's canonical name.
- Distinguishes internal model dependencies from external source tables.
- Produces deterministic JSON or human-readable text reports.
- Calculates transitive downstream impact and shortest dependency distance for one or more changed models.
- Detects dependency cycles and can fail CI with `--fail-on-cycles`.
- Rejects non-query statements, duplicate model names, invalid SQL, empty model directories, oversized files, and symlinks that escape the selected model root.
- Uses stable ordering so generated reports can be diffed and reviewed in pull requests.
- Runs without a database, secrets, network access, or write access to model files.

## Architecture

```text
SQL model directory
       |
       v
Safe file loader ---- file-size / UTF-8 / path-boundary checks
       |
       v
SQLGlot parser ------ dialect-aware syntax tree; CTE names excluded from sources
       |
       v
Dependency resolver - internal model references vs. external tables
       |
       +----> directed dependency graph ----> cycle detection / topological order
       |
       +----> reverse graph ---------------> downstream impact traversal
       |
       v
JSON or text report / CI exit code
```

The graph uses edges from an upstream model to a downstream model. A model's `dependencies` field lists its upstream models; `external_dependencies` lists referenced tables that are not defined by a model file in the selected directory.

## Requirements

- Python 3.12+
- Docker is optional and only needed for container execution.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"

# Analyze the included sample project
lineage-guard analyze --models-dir examples/models --dialect postgres

# Produce a machine-readable report
lineage-guard analyze \
  --models-dir examples/models \
  --dialect postgres \
  --format json \
  --output reports/lineage.json

# Find all downstream models affected by a change to raw_orders
lineage-guard impact \
  --models-dir examples/models \
  --dialect postgres \
  --changed raw_orders \
  --format text
```

## Example output

```text
SQL Lineage Report
Dialect: postgres
Models: 5
Dependency edges: 4
Cycles: none

Build order:
  1. raw_customers
  2. dim_customers
  3. raw_orders
  4. stg_orders
  5. mart_daily_revenue

Models:
  dim_customers
    depends on: raw_customers
    external: landing.customers
  raw_customers
    external: landing.customers
  raw_orders
    external: landing.orders
  stg_orders
    depends on: raw_orders
    external: none
  mart_daily_revenue
    depends on: dim_customers, stg_orders
    external: none
```

The build order is deterministic. Reports generated from the included example files are the source of truth.

## CLI reference

### `analyze`

```text
lineage-guard analyze --models-dir DIR [--dialect DIALECT]
                      [--format text|json] [--output FILE]
                      [--fail-on-cycles]
```

- `--models-dir`: directory recursively scanned for `.sql` model files.
- `--dialect`: SQLGlot dialect name; defaults to `postgres`.
- `--format`: output format; defaults to `text`.
- `--output`: report destination; omitted or `-` writes to standard output. File output is written atomically.
- `--fail-on-cycles`: return exit code `1` if a dependency cycle is found.

### `impact`

```text
lineage-guard impact --models-dir DIR --changed MODEL [--changed MODEL ...]
                     [--dialect DIALECT] [--format text|json] [--output FILE]
```

The command returns all transitive downstream models, ordered by shortest distance from the changed model and then by name. Unknown changed model names are errors; they are not silently ignored.

## SQL model conventions and boundaries

- One SQL query per `.sql` file.
- The filename stem is the model identifier, compared case-insensitively.
- A referenced table whose final identifier matches another model filename is treated as an internal dependency. Other tables are reported as external dependencies.
- CTE aliases are excluded from physical table dependencies.
- This version performs static dependency discovery; it does not infer dependencies from templated SQL, macros, runtime-generated SQL, stored procedures, or application code.
- Schema qualification is retained for external dependencies. Internal model matching uses the final table identifier.
- SQLGlot supports many dialects, but dialect-specific edge cases should be covered by tests before enabling this tool as a hard merge gate in a critical pipeline.

## CI and quality checks

```bash
make install
make lint
make test
make analyze
```

GitHub Actions runs lint, tests, a dependency vulnerability audit, an example analysis, and a Docker build when the project is the repository root. When this project is stored under `projects/sql-lineage-impact-analyzer/` in the portfolio repository, add the job described in [`docs/PORTFOLIO_CI_INTEGRATION.md`](docs/PORTFOLIO_CI_INTEGRATION.md) to the root workflow; GitHub does not discover workflows nested inside a project directory. The CI workflow has read-only repository permissions.

## Docker

```bash
docker build -t sql-lineage-impact-analyzer:local .
docker run --rm \
  -v "$PWD/examples/models:/models:ro" \
  sql-lineage-impact-analyzer:local \
  analyze --models-dir /models --dialect postgres --format text
```

The image runs as a non-root user. Mount model inputs read-only. The tool itself does not need network connectivity.

## Security and operations

See [`docs/SECURITY.md`](docs/SECURITY.md), [`docs/OPERATIONS.md`](docs/OPERATIONS.md), and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). This tool is intentionally a read-only analyzer; do not treat static lineage as a replacement for warehouse query plans, database permissions, or production pipeline validation.

## License

MIT. See [`LICENSE`](LICENSE).
