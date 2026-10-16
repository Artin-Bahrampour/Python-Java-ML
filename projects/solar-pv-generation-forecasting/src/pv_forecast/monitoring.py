"""Lightweight feature-distribution drift checks for batch operations."""

from __future__ import annotations

import numpy as np
import pandas as pd

from pv_forecast.data import FEATURE_COLUMNS


def population_stability_index(
    reference: pd.Series,
    current: pd.Series,
    bins: int = 10,
) -> float:
    """Compute PSI with reference quantile bins and small probability smoothing."""
    if bins < 2:
        raise ValueError("bins must be at least 2")
    reference_values = pd.to_numeric(reference, errors="coerce").to_numpy(dtype=float)
    current_values = pd.to_numeric(current, errors="coerce").to_numpy(dtype=float)
    reference_values = reference_values[np.isfinite(reference_values)]
    current_values = current_values[np.isfinite(current_values)]
    if reference_values.size == 0 or current_values.size == 0:
        raise ValueError("reference and current samples must contain finite values")

    edges = np.unique(np.quantile(reference_values, np.linspace(0.0, 1.0, bins + 1)))
    if edges.size == 1:
        value = float(edges[0])
        margin = max(abs(value) * 1e-6, 1e-6)
        edges = np.array([-np.inf, value - margin, value + margin, np.inf])
    elif edges.size == 2:
        split_value = float(np.mean(edges))
        edges = np.array([-np.inf, split_value, np.inf])
    edges[0] = -np.inf
    edges[-1] = np.inf
    reference_counts = np.histogram(reference_values, bins=edges)[0].astype(float)
    current_counts = np.histogram(current_values, bins=edges)[0].astype(float)
    smoothing = 1e-6
    reference_share = (reference_counts + smoothing) / (
        reference_counts.sum() + smoothing * len(reference_counts)
    )
    current_share = (current_counts + smoothing) / (
        current_counts.sum() + smoothing * len(current_counts)
    )
    contribution = (current_share - reference_share) * np.log(current_share / reference_share)
    return float(np.sum(contribution))


def feature_drift_report(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    threshold: float = 0.2,
) -> dict[str, object]:
    """Summarize PSI per feature; thresholds are heuristics, not statistical tests."""
    if threshold <= 0:
        raise ValueError("threshold must be positive")
    missing_reference = sorted(set(FEATURE_COLUMNS) - set(reference.columns))
    missing_current = sorted(set(FEATURE_COLUMNS) - set(current.columns))
    if missing_reference or missing_current:
        raise ValueError(
            f"missing feature columns; reference={missing_reference}, current={missing_current}"
        )

    features: dict[str, dict[str, float | bool]] = {}
    for column in FEATURE_COLUMNS:
        psi = population_stability_index(reference[column], current[column])
        features[column] = {"psi": psi, "drift_flag": psi >= threshold}
    return {
        "reference_rows": int(len(reference)),
        "current_rows": int(len(current)),
        "psi_threshold": float(threshold),
        "interpretation": "PSI is a heuristic indicator; investigate flagged features in context.",
        "features": features,
        "drifted_features": sorted(
            name for name, result in features.items() if result["drift_flag"]
        ),
    }
