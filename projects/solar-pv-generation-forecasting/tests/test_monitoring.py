import pandas as pd
import pytest

from pv_forecast.data import generate_dataset
from pv_forecast.monitoring import feature_drift_report, population_stability_index


def test_identical_samples_have_near_zero_psi():
    frame = generate_dataset(days=45)
    psi = population_stability_index(frame["cloud_cover_forecast"], frame["cloud_cover_forecast"])
    assert psi < 1e-9


def test_shifted_distribution_has_positive_psi():
    reference = generate_dataset(days=45)
    current = reference.copy()
    current["temperature_forecast_c"] += 15.0
    report = feature_drift_report(reference, current)
    assert report["features"]["temperature_forecast_c"]["psi"] > 0.2
    assert "temperature_forecast_c" in report["drifted_features"]


def test_constant_reference_detects_shift():
    reference = pd.Series([1.0] * 30)
    current = pd.Series([2.0] * 30)
    assert population_stability_index(reference, current) > 0.2


def test_two_value_reference_detects_shift():
    reference = pd.Series([0.0, 1.0] * 20)
    current = pd.Series([2.0, 3.0] * 20)
    assert population_stability_index(reference, current) > 0.2


def test_invalid_bins_are_rejected():
    with pytest.raises(ValueError, match="at least 2"):
        population_stability_index(pd.Series([1, 2]), pd.Series([1, 2]), bins=1)
