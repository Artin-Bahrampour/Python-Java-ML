from app.train import synthetic_data, train


def test_training_artifact_has_operational_metrics():
    bundle, metrics = train(synthetic_data(500))
    assert 0.1 <= bundle["threshold"] <= 0.9
    assert 0 <= metrics["validation_average_precision"] <= 1
