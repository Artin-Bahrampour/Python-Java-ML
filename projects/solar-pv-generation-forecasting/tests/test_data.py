import pandas as pd
import pytest

from pv_forecast.data import FEATURE_COLUMNS, TARGET_COLUMN, generate_dataset, validate_frame


def test_generation_is_deterministic():
    first = generate_dataset(days=60, seed=7)
    second = generate_dataset(days=60, seed=7)
    pd.testing.assert_frame_equal(first, second)


def test_generator_produces_valid_nonnegative_target():
    frame = generate_dataset(days=45)
    assert set(FEATURE_COLUMNS).issubset(frame.columns)
    assert frame[TARGET_COLUMN].between(0, 5.5).all()
    assert frame["timestamp"].is_monotonic_increasing


def test_invalid_cloud_cover_is_rejected():
    frame = generate_dataset(days=45)
    frame.loc[0, "cloud_cover_forecast"] = 1.5
    with pytest.raises(ValueError, match="cloud_cover_forecast"):
        validate_frame(frame)


def test_duplicate_timestamps_are_rejected():
    frame = generate_dataset(days=45)
    frame.loc[1, "timestamp"] = frame.loc[0, "timestamp"]
    with pytest.raises(ValueError, match="unique"):
        validate_frame(frame)


def test_missing_target_is_rejected():
    frame = generate_dataset(days=45).drop(columns=[TARGET_COLUMN])
    with pytest.raises(ValueError, match="missing required columns"):
        validate_frame(frame)
