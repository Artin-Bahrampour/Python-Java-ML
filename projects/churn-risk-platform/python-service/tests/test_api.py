from fastapi.testclient import TestClient
from app import api
from app.train import synthetic_data, train


def test_prediction(monkeypatch, tmp_path):
    import joblib
    artifact, _ = train(synthetic_data(300))
    path = tmp_path / "model.joblib"; joblib.dump(artifact, path)
    monkeypatch.setattr(api, "MODEL_PATH", path)
    response = TestClient(api.app).post("/v1/predict", json={"customer_id":"c-1","tenure_months":2,"monthly_charge":99,"support_tickets_90d":4,"login_days_30d":1,"contract_type":"month_to_month","payment_method":"invoice","autopay_enabled":False})
    assert response.status_code == 200
    assert 0 <= response.json()["churn_probability"] <= 1
