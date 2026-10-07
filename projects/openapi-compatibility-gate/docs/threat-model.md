# Threat model

## Assets

- CI reliability and release decisions based on compatibility findings.
- Repository integrity and generated report integrity.
- Developer workstations running the CLI on reviewed API contracts.

## Trust boundaries

Input OpenAPI files are untrusted. The tool reads local files only and must not execute content from the specification.

## Controls

- YAML uses `yaml.safe_load`, not arbitrary Python object constructors.
- Input files are limited to 5 MiB and must decode as UTF-8.
- External `$ref` targets are not fetched, preventing network access and SSRF through remote references.
- Reports are written through a temporary file and atomically replaced.
- GitHub Actions receives read-only repository permissions.
- The Docker image runs as a non-root user.

## Residual risks and limitations

The tool is not a complete OpenAPI conformance validator. Teams should validate specifications separately and review findings before making release decisions. Dependency updates should be reviewed and tested. File-system permissions and the integrity of the CI runner remain deployment responsibilities.
