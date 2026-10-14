import numpy as np
import pytest

from churn_ml.data import generate_customers
from churn_ml.modeling import evaluate, load_bundle, train_and_evaluate


def test_metrics_are_in_valid_ranges():
    report = evaluate(np.array([0, 0, 1, 1]), np.array([0.1, 0.4, 0.6, 0.9]))
    assert 0 <= report["roc_auc"] <= 1 and 0 <= report["average_precision"] <= 1


def test_invalid_probabilities_rejected():
    with pytest.raises(ValueError, match="between 0 and 1"):
        evaluate(np.array([0, 1]), np.array([0.2, 1.5]))


def test_training_bundle_round_trip(tmp_path):
    report = train_and_evaluate(generate_customers(600), tmp_path)
    bundle = load_bundle(tmp_path / "model_bundle.joblib")
    assert report["selected_model"] in bundle["models"]
    assert np.isfinite(
        bundle["models"][bundle["selected_model"]].predict_proba(
            generate_customers(600)[bundle["feature_columns"]].iloc[:5]
        )
    ).all()
