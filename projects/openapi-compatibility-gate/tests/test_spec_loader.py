import json

import pytest

from oacg.errors import SpecLoadError, SpecValidationError
from oacg.spec_loader import load_spec


def test_loads_yaml(tmp_path):
    path = tmp_path / "api.yaml"
    path.write_text("openapi: 3.0.3\ninfo:\n  title: Demo\n  version: '1'\npaths: {}\n", encoding="utf-8")
    assert load_spec(path)["openapi"] == "3.0.3"


def test_loads_json(tmp_path):
    path = tmp_path / "api.json"
    path.write_text(json.dumps({"openapi": "3.1.0", "paths": {}}), encoding="utf-8")
    assert load_spec(path)["openapi"] == "3.1.0"


def test_rejects_non_openapi_root(tmp_path):
    path = tmp_path / "api.yaml"
    path.write_text("- item\n", encoding="utf-8")
    with pytest.raises(SpecValidationError):
        load_spec(path)


def test_rejects_unsupported_version(tmp_path):
    path = tmp_path / "api.yaml"
    path.write_text("openapi: 2.0\npaths: {}\n", encoding="utf-8")
    with pytest.raises(SpecValidationError, match="Only OpenAPI"):
        load_spec(path)


def test_rejects_malformed_yaml(tmp_path):
    path = tmp_path / "api.yaml"
    path.write_text("openapi: [\n", encoding="utf-8")
    with pytest.raises(SpecLoadError):
        load_spec(path)


def test_rejects_missing_file(tmp_path):
    with pytest.raises(SpecLoadError, match="Cannot read"):
        load_spec(tmp_path / "missing.yaml")


def test_rejects_empty_file(tmp_path):
    path = tmp_path / "empty.yaml"
    path.write_bytes(b"")
    with pytest.raises(SpecLoadError, match="empty"):
        load_spec(path)


def test_rejects_non_utf8_file(tmp_path):
    path = tmp_path / "invalid.yaml"
    path.write_bytes(b"\xff\xfe")
    with pytest.raises(SpecLoadError, match="UTF-8"):
        load_spec(path)


def test_rejects_invalid_paths_type(tmp_path):
    path = tmp_path / "api.yaml"
    path.write_text("openapi: 3.0.3\npaths: []\n", encoding="utf-8")
    with pytest.raises(SpecValidationError, match="paths"):
        load_spec(path)


def test_rejects_invalid_components_type(tmp_path):
    path = tmp_path / "api.yaml"
    path.write_text("openapi: 3.0.3\npaths: {}\ncomponents: []\n", encoding="utf-8")
    with pytest.raises(SpecValidationError, match="components"):
        load_spec(path)


def test_rejects_spec_over_size_limit(tmp_path, monkeypatch):
    import oacg.spec_loader as loader

    path = tmp_path / "large.yaml"
    path.write_text("openapi: 3.0.3\npaths: {}\n", encoding="utf-8")
    monkeypatch.setattr(loader, "MAX_SPEC_BYTES", 2)
    with pytest.raises(SpecLoadError, match="size limit"):
        load_spec(path)
