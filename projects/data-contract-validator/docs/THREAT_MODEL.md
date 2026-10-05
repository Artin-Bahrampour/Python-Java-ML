# Threat Model

- **Untrusted input:** datasets and contracts are treated as untrusted; paths are supplied by the caller and no shell execution occurs.
- **Resource exhaustion:** production deployments should add streaming/chunk limits for very large files and enforce process memory/CPU limits at the container or job level.
- **Sensitive data:** reports may contain row numbers and profiling metadata but should not be configured to persist raw values. Operators should apply normal storage access controls.
- **Supply chain:** dependencies are intentionally minimal; CI should pin/lock dependencies for a controlled production build.
