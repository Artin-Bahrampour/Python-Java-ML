import joblib
from fastapi.testclient import TestClient
from app import api
from app.train import synthetic_data, train


def test_risk_endpoint(monkeypatch, tmp_path):
    bundle, _ = train(synthetic_data(500))
    path = tmp_path / "model.joblib"; joblib.dump(bundle, path)
    monkeypatch.setattr(api, "MODEL_PATH", path)
    response = TestClient(api.app).post("/v1/risk", json={"asset_id":"P-1","asset_type":"centrifugal_pump","operating_hours":5200,"mean_vibration_mm_s":5.2,"temperature_c":77,"pressure_bar":8.3,"starts_24h":6,"lubricant_age_days":90})
    assert response.status_code == 200
    assert 0 <= response.json()["failure_risk_14d"] <= 1
