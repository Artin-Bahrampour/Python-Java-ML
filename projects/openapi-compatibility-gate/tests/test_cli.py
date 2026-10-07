import json

from oacg.cli import EXIT_BREAKING, EXIT_COMPATIBLE, EXIT_INPUT_ERROR, main


def write_spec(path, body):
    path.write_text(json.dumps(body), encoding="utf-8")


def test_cli_success_and_report(tmp_path, capsys):
    document = {"openapi": "3.0.3", "info": {"title": "x", "version": "1"}, "paths": {}}
    baseline, candidate, report = tmp_path / "base.json", tmp_path / "next.json", tmp_path / "report.json"
    write_spec(baseline, document)
    write_spec(candidate, document)
    assert main([str(baseline), str(candidate), "--report", str(report)]) == EXIT_COMPATIBLE
    assert json.loads(report.read_text(encoding="utf-8"))["summary"]["compatible"] is True
    assert "COMPATIBLE" in capsys.readouterr().out


def test_cli_breaking_exit_code(tmp_path):
    baseline = tmp_path / "base.json"
    candidate = tmp_path / "next.json"
    write_spec(baseline, {"openapi": "3.0.3", "paths": {"/x": {"get": {"responses": {"200": {"description": "OK"}}}}}})
    write_spec(candidate, {"openapi": "3.0.3", "paths": {}})
    assert main([str(baseline), str(candidate), "--quiet"]) == EXIT_BREAKING


def test_cli_input_error(tmp_path, capsys):
    assert main([str(tmp_path / "missing.yaml"), str(tmp_path / "also-missing.yaml")]) == EXIT_INPUT_ERROR
    assert "ERROR:" in capsys.readouterr().err


def test_warning_can_fail_build(tmp_path):
    baseline = {"openapi": "3.0.3", "paths": {"/x": {"get": {"responses": {"200": {"description": "OK", "content": {"application/json": {"schema": {"type": "object", "properties": {"id": {"type": "string"}, "name": {"type": "string"}}}}}}}}}}}
    candidate = {"openapi": "3.0.3", "paths": {"/x": {"get": {"responses": {"200": {"description": "OK", "content": {"application/json": {"schema": {"type": "object", "properties": {"id": {"type": "string"}}}}}}}}}}}
    b, c = tmp_path / "b.json", tmp_path / "c.json"
    write_spec(b, baseline)
    write_spec(c, candidate)
    assert main([str(b), str(c), "--fail-on-warning", "--quiet"]) == EXIT_BREAKING


def test_fail_on_warning_prints_failed_build_status(tmp_path, capsys):
    baseline = {"openapi": "3.0.3", "paths": {"/x": {"get": {"responses": {"200": {"description": "OK", "content": {"application/json": {"schema": {"type": "object", "properties": {"id": {"type": "string"}, "name": {"type": "string"}}}}}}}}}}}
    candidate = {"openapi": "3.0.3", "paths": {"/x": {"get": {"responses": {"200": {"description": "OK", "content": {"application/json": {"schema": {"type": "object", "properties": {"id": {"type": "string"}}}}}}}}}}}
    b, c = tmp_path / "b.json", tmp_path / "c.json"
    write_spec(b, baseline)
    write_spec(c, candidate)
    assert main([str(b), str(c), "--fail-on-warning", "--quiet"]) == EXIT_BREAKING
    assert "WARNINGS FAILED BUILD" in capsys.readouterr().out
