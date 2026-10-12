"""Filesystem orchestration for SQL model analysis."""

from __future__ import annotations

from pathlib import Path

from .errors import ModelLoadError
from .graph import LineageReport, ParsedModel, build_report
from .sql_parser import parse_model_sql, read_model_file


def analyze_directory(models_dir: Path, dialect: str = "postgres") -> LineageReport:
    """Load, parse, and analyze every SQL model beneath ``models_dir``."""
    try:
        root = models_dir.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        message = f"Model directory does not exist or cannot be resolved: {models_dir}"
        raise ModelLoadError(message) from exc
    if not root.is_dir():
        raise ModelLoadError(f"Model path is not a directory: {models_dir}")

    files = sorted(path for path in root.rglob("*.sql") if path.is_file())
    if not files:
        raise ModelLoadError(f"No .sql model files found under: {models_dir}")

    parsed: list[ParsedModel] = []
    for path in files:
        content = read_model_file(path, root)
        relative = path.relative_to(root).as_posix()
        name = path.stem.casefold()
        references = parse_model_sql(content, relative, dialect)
        parsed.append(ParsedModel(name=name, file=relative, references=tuple(sorted(references))))
    return build_report(parsed, dialect)
