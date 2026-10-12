from pathlib import Path

import pytest

from lineage_guard.analyzer import analyze_directory
from lineage_guard.errors import ModelLoadError, ModelParseError


def test_example_models_form_expected_dependency_graph():
    root = Path(__file__).parents[1] / "examples" / "models"
    report = analyze_directory(root, "postgres")
    by_name = {model.name: model for model in report.models}
    assert len(report.models) == 5
    assert by_name["stg_orders"].dependencies == ("raw_orders",)
    assert by_name["mart_daily_revenue"].dependencies == (
        "dim_customers",
        "stg_orders",
    )
    assert not report.cycles
    assert set(report.topological_order) == set(by_name)
    assert report.topological_order == (
        "raw_customers",
        "dim_customers",
        "raw_orders",
        "stg_orders",
        "mart_daily_revenue",
    )


def test_empty_directory_is_rejected(tmp_path):
    with pytest.raises(ModelLoadError, match="No .sql model files"):
        analyze_directory(tmp_path)


def test_non_query_model_is_rejected(tmp_path):
    (tmp_path / "bad.sql").write_text("DELETE FROM customers", encoding="utf-8")
    with pytest.raises(ModelParseError, match="only read-only query"):
        analyze_directory(tmp_path)


def test_symlink_escape_is_rejected(tmp_path):
    root = tmp_path / "models"
    root.mkdir()
    outside = tmp_path / "outside.sql"
    outside.write_text("SELECT 1 AS value", encoding="utf-8")
    link = root / "escape.sql"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks are unavailable on this platform")
    with pytest.raises(ModelLoadError, match="escapes the configured root"):
        analyze_directory(root)
