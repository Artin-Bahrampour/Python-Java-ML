from app.train import synthetic_data, train


def test_training_creates_usable_bundle():
    bundle, metrics = train(synthetic_data(300))
    assert 0.2 <= bundle["threshold"] <= 0.8
    assert 0.0 <= metrics["validation_auc"] <= 1.0
