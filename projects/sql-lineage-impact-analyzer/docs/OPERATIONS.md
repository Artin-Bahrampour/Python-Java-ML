# Operations

## Local verification

```bash
python -m pip install -e ".[dev]"
ruff check src tests
pytest -q
lineage-guard analyze --models-dir examples/models --dialect postgres --format json --output reports/lineage.json
lineage-guard impact --models-dir examples/models --changed raw_orders --dialect postgres
```

## CI integration

Run `lineage-guard analyze --models-dir <path> --dialect postgres --fail-on-cycles` in the repository's SQL model directory. A non-zero result blocks a merge when parsing fails or a cycle is detected. External dependencies are informational by default because source tables commonly live outside the model directory.

Store the JSON report as a build artifact if reviewers need a machine-readable snapshot. Avoid committing generated reports unless the team explicitly wants reviewed lineage snapshots in source control.

## Exit codes

- `0`: analysis or impact report generated successfully.
- `1`: analysis completed but `--fail-on-cycles` found one or more cycles.
- `2`: invalid input, SQL parse failure, unsupported statement, unknown model, or output error.

## Operational recommendations

- Pin Python and review dependency updates regularly.
- Review the generated dependency graph when introducing macros, new dialect constructs, or cross-schema naming conventions.
- Keep model files small enough for static review; the loader rejects any individual file larger than 2 MB.
- Treat output reports as potentially sensitive metadata: table names can reveal business concepts even though row data is never read.
- In production CI, run the tool in a container without warehouse credentials and mount the model directory read-only.
