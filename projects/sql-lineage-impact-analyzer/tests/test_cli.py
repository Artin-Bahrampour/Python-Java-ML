import json
from pathlib import Path

from lineage_guard.cli import main


def example_dir() -> Path:
    return Path(__file__).parents[1] / "examples" / "models"


def test_analyze_json_to_file_is_valid_and_deterministic(tmp_path):
    output = tmp_path / "reports" / "lineage.json"
    code = main(
        [
            "analyze",
            "--models-dir",
            str(example_dir()),
            "--dialect",
            "postgres",
            "--format",
            "json",
            "--output",
            str(output),
        ]
    )
    assert code == 0
    first = output.read_text(encoding="utf-8")
    payload = json.loads(first)
    assert payload["schema_version"] == 1
    assert len(payload["models"]) == 5
    assert (
        main(
            [
                "analyze",
                "--models-dir",
                str(example_dir()),
                "--dialect",
                "postgres",
                "--format",
                "json",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    assert output.read_text(encoding="utf-8") == first


def test_impact_command_writes_expected_downstream_models(capsys):
    code = main(
        [
            "impact",
            "--models-dir",
            str(example_dir()),
            "--changed",
            "raw_orders",
            "--format",
            "text",
        ]
    )
    output = capsys.readouterr().out
    assert code == 0
    assert "stg_orders" in output
    assert "mart_daily_revenue" in output


def test_cycle_policy_returns_one(tmp_path, capsys):
    (tmp_path / "alpha.sql").write_text("SELECT * FROM beta", encoding="utf-8")
    (tmp_path / "beta.sql").write_text("SELECT * FROM alpha", encoding="utf-8")
    code = main(
        [
            "analyze",
            "--models-dir",
            str(tmp_path),
            "--fail-on-cycles",
        ]
    )
    assert code == 1
    assert "Cycles: 1" in capsys.readouterr().out
