# Integrating CI into the Python-Java-ML portfolio repository

GitHub only loads workflow files from the repository-level `.github/workflows/` directory. The project's own `.github/workflows/ci.yml` is active when the project is a standalone repository, but **will not run automatically** after the ZIP is extracted into `projects/sql-lineage-impact-analyzer/`.

To test this project in the portfolio repository, add the following independent job under `jobs:` in the repository-root `.github/workflows/ci.yml`. Keep the existing jobs unchanged. The separate Python 3.12 job avoids changing the interpreter used by existing projects.

```yaml
  sql-lineage-impact-analyzer:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: projects/sql-lineage-impact-analyzer
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: projects/sql-lineage-impact-analyzer/requirements-dev.txt
      - name: Install project and development dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e ".[dev]"
      - name: Lint
        run: ruff check src tests
      - name: Test
        run: pytest -q
      - name: Audit dependencies
        run: pip-audit
      - name: Verify example analysis
        run: lineage-guard analyze --models-dir examples/models --dialect postgres --fail-on-cycles --format json --output /tmp/lineage-report.json
      - name: Build container
        run: docker build -t sql-lineage-impact-analyzer:ci .
```

The project upload process should therefore include a separate, reviewed edit to the root workflow. Do not assume the nested workflow ran merely because its file exists.
