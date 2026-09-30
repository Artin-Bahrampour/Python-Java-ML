from fastapi.testclient import TestClient

from health_anomaly.api import app, detector

client = TestClient(app)


def setup_function() -> None:
    detector._state.model = None
    detector._state.samples = 0


def test_health_before_training() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "model_ready": False}


def test_train_and_score() -> None:
    observations = [
        {
            "latency_ms": 100 + i,
            "error_rate": 0.01 + i * 0.001,
            "cpu_percent": 40 + i,
            "requests_per_minute": 500 + i * 5,
        }
        for i in range(10)
    ]

    train_response = client.post(
        "/v1/model/train",
        json={"observations": observations},
    )

    assert train_response.status_code == 200
    assert train_response.json()["trained"] is True

    score_response = client.post(
        "/v1/anomalies/score",
        json={"observations": [observations[0]]},
    )

    assert score_response.status_code == 200
    assert len(score_response.json()["results"]) == 1
