from health_anomaly.features import to_matrix
from health_anomaly.schemas import Telemetry


def test_to_matrix_preserves_feature_order() -> None:
    observation = Telemetry(
        latency_ms=100,
        error_rate=0.02,
        cpu_percent=50,
        requests_per_minute=400,
    )

    matrix = to_matrix([observation])

    assert matrix.shape == (1, 4)
    assert matrix[0].tolist() == [100.0, 0.02, 50.0, 400.0]
