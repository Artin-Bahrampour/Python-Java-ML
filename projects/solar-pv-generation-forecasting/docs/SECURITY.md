# Security Notes

- No credentials, external API tokens, or production datasets are required.
- Keep real site data and generated model artifacts out of version control.
- The CLI reads local CSV files and writes local outputs; it does not open network listeners.
- The Docker image uses a non-root account. The Compose example enables a read-only root filesystem, drops Linux capabilities, and disables privilege escalation.
- Treat `joblib` model bundles as trusted executable serialization artifacts. Do not load bundles from untrusted sources.
- Pin and review dependency updates in a controlled environment before production use.
- Before operational deployment, define access controls, artifact provenance, retention rules, and audit logging.
