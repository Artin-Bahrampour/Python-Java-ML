from datetime import datetime, timezone


def payload():
    return {
        "service": "payments-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "latency_ms": 120,
        "error_rate": 0.01,
        "requests_per_minute": 200,
        "cpu_percent": 45,
        "memory_percent": 55,
    }


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ingest(client):
    response = client.post("/v1/telemetry", json=payload())
    assert response.status_code == 201
    assert response.json()["service"] == "payments-api"


def test_validation_rejects_invalid_error_rate(client):
    data = payload()
    data["error_rate"] = 1.5
    response = client.post("/v1/telemetry", json=data)
    assert response.status_code == 422


def test_summary_empty_service(client):
    response = client.get("/v1/services/unknown-api/summary")
    assert response.status_code == 200
    assert response.json()["samples"] == 0
