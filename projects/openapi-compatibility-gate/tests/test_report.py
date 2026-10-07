import json

from oacg.models import ComparisonReport, Finding
from oacg.report import write_report


def test_report_is_json_and_creates_parent_directories(tmp_path):
    report = ComparisonReport("old.yaml", "new.yaml", (Finding("PATH_REMOVED", "breaking", "/paths/~1x", "Removed"),))
    target = tmp_path / "nested" / "report.json"
    write_report(report, target)
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["summary"]["compatible"] is False
    assert payload["findings"][0]["rule_id"] == "PATH_REMOVED"
