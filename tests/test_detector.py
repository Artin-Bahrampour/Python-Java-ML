import pytest

from health_anomaly.detector import AnomalyDetector
from health_anomaly.schemas import Telemetry


def normal_observations() -> list[Telemetry]:
    return [
        Telemetry(
            latency_ms=100 + i,
            error_rate=0.01 + i * 0.001,
            cpu_percent=40 + i,
            requests_per_minute=500 + i * 5,
        )
        for i in range(10)
    ]


def test_detector_requires_training() -> None:
    detector = AnomalyDetector()

    with pytest.raises(RuntimeError, match="not been trained"):
        detector.score(normal_observations()[:1])


def test_detector_trains_and_scores() -> None:
    detector = AnomalyDetector()
    detector.train(normal_observations())

    results = detector.score(
        [
            Telemetry(
                latency_ms=105,
                error_rate=0.015,
                cpu_percent=45,
                requests_per_minute=525,
            )
        ]
    )

    assert len(results) == 1
    assert isinstance(results[0].score, float)
    assert isinstance(results[0].anomaly, bool)
