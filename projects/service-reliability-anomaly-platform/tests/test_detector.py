from types import SimpleNamespace
from app.ml import AnomalyDetector


def record(value):
    return SimpleNamespace(
        latency_ms=value,
        error_rate=value / 1000,
        requests_per_minute=200 if value < 500 else 20,
        cpu_percent=45 if value < 500 else 98,
        memory_percent=55 if value < 500 else 95,
    )


def test_detector_finds_extreme_observation(tmp_path):
    detector = AnomalyDetector(str(tmp_path / "model.joblib"), 0.1)
    normal = [record(100 + i) for i in range(30)]
    detector.train(normal)
    scores = detector.score(normal + [record(1500)])
    assert scores[-1][1] is True
