import pandas as pd
import pytest

from churn_ml.data import generate_customers, validate_frame


def test_generation_is_deterministic():
    pd.testing.assert_frame_equal(generate_customers(500, 7), generate_customers(500, 7))


def test_generated_data_contains_both_classes():
    assert set(generate_customers(1000)["churned"].unique()) == {0, 1}


def test_invalid_usage_is_rejected():
    frame = generate_customers(300)
    frame.loc[0, "usage_days_30d"] = 31
    with pytest.raises(ValueError, match="between 0 and 30"):
        validate_frame(frame)


def test_unknown_plan_is_rejected():
    frame = generate_customers(300)
    frame.loc[0, "plan_type"] = "enterprise"
    with pytest.raises(ValueError, match="unsupported"):
        validate_frame(frame)
