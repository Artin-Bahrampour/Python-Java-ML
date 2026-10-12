"""Dialect-aware SQL parsing and physical table-reference extraction."""

from __future__ import annotations

from pathlib import Path

import sqlglot
from sqlglot import exp
from sqlglot.errors import ErrorLevel, ParseError

from .errors import ModelLoadError, ModelParseError

MAX_SQL_FILE_BYTES = 2_000_000


def read_model_file(path: Path, root: Path) -> str:
    """Read a SQL file only if it resolves inside the configured model root."""
    try:
        resolved_root = root.resolve(strict=True)
        resolved_path = path.resolve(strict=True)
        if not resolved_path.is_relative_to(resolved_root):
            raise ModelLoadError(f"Model path escapes the configured root: {path}")
        if not resolved_path.is_file():
            raise ModelLoadError(f"Model path is not a regular file: {path}")
        size = resolved_path.stat().st_size
        if size > MAX_SQL_FILE_BYTES:
            raise ModelLoadError(f"SQL file exceeds the {MAX_SQL_FILE_BYTES}-byte limit: {path}")
        return resolved_path.read_text(encoding="utf-8")
    except ModelLoadError:
        raise
    except (OSError, UnicodeError, RuntimeError) as exc:
        raise ModelLoadError(f"Unable to read SQL model {path}: {exc}") from exc


def parse_model_sql(sql_text: str, path: str, dialect: str) -> set[str]:
    """Return normalized physical table references from exactly one query."""
    if not sql_text.strip():
        raise ModelParseError(f"{path}: SQL file is empty")

    try:
        statements = [
            statement
            for statement in sqlglot.parse(
                sql_text,
                read=dialect,
                error_level=ErrorLevel.RAISE,
            )
            if statement is not None
        ]
    except (ParseError, ValueError) as exc:
        raise ModelParseError(f"{path}: SQL parse failed for dialect '{dialect}': {exc}") from exc

    if len(statements) != 1:
        raise ModelParseError(
            f"{path}: expected exactly one SQL statement, found {len(statements)}"
        )

    statement = statements[0]
    if not isinstance(statement, exp.Query):
        raise ModelParseError(
            f"{path}: only read-only query statements (SELECT/CTE/set operations) are supported"
        )

    cte_names = {
        cte.alias_or_name.casefold() for cte in statement.find_all(exp.CTE) if cte.alias_or_name
    }
    references: set[str] = set()
    for table in statement.find_all(exp.Table):
        table_name = table.name
        if not table_name or table_name.casefold() in cte_names:
            continue
        parts = [part.casefold() for part in (table.catalog, table.db, table_name) if part]
        if parts:
            references.add(".".join(parts))
    return references
