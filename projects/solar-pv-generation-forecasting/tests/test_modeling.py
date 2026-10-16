import numpy as np
import pytest

from pv_forecast.data import generate_dataset
from pv_forecast.modeling import (
    load_bundle,
    predict_frame,
    regression_metrics,
    temporal_partitions,
    train_and_evaluate,
)


def test_metrics_are_valid_and_finite():
    metrics = regression_metrics(np.array([0.0, 1.0, 2.0]), np.array([0.1, 0.9, 2.1]))
    assert metrics["mae_kwh"] >= 0
    assert metrics["rmse_kwh"] >= 0
    assert np.isfinite(metrics["r2"])


def test_invalid_metrics_inputs_are_rejected():
    with pytest.raises(ValueError, match="equal in length"):
        regression_metrics(np.array([1.0]), np.array([1.0, 2.0]))


def test_temporal_partitions_do_not_overlap():
    frame = generate_dataset(days=90)
    train, validation, test = temporal_partitions(frame)
    assert train["timestamp"].max() < validation["timestamp"].min()
    assert validation["timestamp"].max() < test["timestamp"].min()


def test_training_bundle_round_trip_and_test_report(tmp_path):
    frame = generate_dataset(days=120, seed=13)
    report = train_and_evaluate(frame, tmp_path, seed=13)
    bundle = load_bundle(tmp_path / "model_bundle.joblib")
    assert report["selected_model"] in {"hist_gradient_boosting", "random_forest"}
    assert "seasonal_naive_24h" in report["test_metrics"]
    assert bundle["selected_model_name"] == report["selected_model"]
    predictions = predict_frame(frame.tail(10), bundle)
    assert len(predictions) == 10
    assert predictions["predicted_generation_kwh"].notna().all()
    assert (tmp_path / "metrics.json").exists()
