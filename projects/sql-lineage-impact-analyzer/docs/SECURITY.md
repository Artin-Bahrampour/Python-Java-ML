# Security considerations

## Threat model

The tool analyzes SQL text from a repository. It does not connect to a database, evaluate SQL, import project code, or execute shell commands from model content.

Controls included:

- Model files are resolved and checked to remain inside the configured root, preventing a symlink from being used to read an arbitrary external file.
- Files larger than 2 MB are rejected before reading their content.
- Files must decode as UTF-8.
- Only one query statement is accepted; DDL/DML statements are rejected.
- Report files are written via a temporary file and atomic replacement.
- The Docker image uses a dedicated non-root user.
- GitHub Actions receives only `contents: read` permission.
- Dependency audit is part of CI.

## Limitations

Static SQL parsing is not a security boundary for executing queries. Never execute model SQL simply because this tool accepted it. Reports expose model and table identifiers; handle them according to repository confidentiality requirements. SQL templates and macros are not rendered, so the graph may be incomplete when dependencies are generated dynamically.

## Dependency hygiene

Review `pip-audit` results in CI and update the supported SQLGlot range after testing parser compatibility. Avoid installing dependencies from untrusted package indexes.
