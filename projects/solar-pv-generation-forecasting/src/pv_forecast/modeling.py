"""Leakage-aware temporal model selection and evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from pv_forecast.data import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    TIMESTAMP_COLUMN,
    validate_frame,
)

BASELINE_NAME = "seasonal_naive_24h"


def regression_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    """Compute standard regression metrics, rejecting malformed predictions."""
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    if actual.size == 0 or actual.size != predicted.size:
        raise ValueError("actual and predicted arrays must be non-empty and equal in length")
    if not np.isfinite(actual).all() or not np.isfinite(predicted).all():
        raise ValueError("actual and predicted arrays must contain only finite values")
    return {
        "mae_kwh": float(mean_absolute_error(actual, predicted)),
        "rmse_kwh": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
    }


def temporal_partitions(
    frame: pd.DataFrame,
    train_fraction: float = 0.70,
    validation_fraction: float = 0.15,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split chronologically; never shuffle time-series rows."""
    if not 0.0 < train_fraction < 1.0:
        raise ValueError("train_fraction must be between 0 and 1")
    if not 0.0 < validation_fraction < 1.0:
        raise ValueError("validation_fraction must be between 0 and 1")
    if train_fraction + validation_fraction >= 1.0:
        raise ValueError("train and validation fractions must sum to less than 1")
    if len(frame) < 100:
        raise ValueError("at least 100 rows are required for temporal partitioning")

    ordered = frame.sort_values(TIMESTAMP_COLUMN).reset_index(drop=True)
    train_end = int(len(ordered) * train_fraction)
    validation_end = int(len(ordered) * (train_fraction + validation_fraction))
    train = ordered.iloc[:train_end].copy()
    validation = ordered.iloc[train_end:validation_end].copy()
    test = ordered.iloc[validation_end:].copy()
    if min(len(train), len(validation), len(test)) == 0:
        raise ValueError("temporal split produced an empty partition")
    return train, validation, test


def _build_candidates(seed: int) -> dict[str, Any]:
    return {
        "hist_gradient_boosting": HistGradientBoostingRegressor(
            learning_rate=0.08,
            max_iter=180,
            max_leaf_nodes=20,
            l2_regularization=1.0,
            random_state=seed,
        ),
        "random_forest": RandomForestRegressor(
            n_estimators=120,
            min_samples_leaf=3,
            max_features=0.9,
            n_jobs=-1,
            random_state=seed,
        ),
    }


def train_and_evaluate(
    frame: pd.DataFrame,
    artifacts_dir: str | Path,
    seed: int = 42,
) -> dict[str, Any]:
    """Select on validation MAE, refit on train+validation, and evaluate once on test."""
    frame = validate_frame(frame, require_target=True)
    train, validation, test = temporal_partitions(frame)
    candidates = _build_candidates(seed)
    validation_reports: dict[str, dict[str, float]] = {
        BASELINE_NAME: regression_metrics(
            validation[TARGET_COLUMN].to_numpy(),
            validation["lag_24h_kwh"].to_numpy(),
        )
    }
    for name, model in candidates.items():
        model.fit(train[FEATURE_COLUMNS], train[TARGET_COLUMN])
        validation_reports[name] = regression_metrics(
            validation[TARGET_COLUMN].to_numpy(),
            model.predict(validation[FEATURE_COLUMNS]),
        )

    selected_name = min(
        candidates,
        key=lambda name: validation_reports[name]["mae_kwh"],
    )
    development = pd.concat([train, validation], ignore_index=True)
    selected_model = _build_candidates(seed)[selected_name]
    selected_model.fit(development[FEATURE_COLUMNS], development[TARGET_COLUMN])

    test_actual = test[TARGET_COLUMN].to_numpy()
    test_prediction = selected_model.predict(test[FEATURE_COLUMNS])
    test_reports = {
        BASELINE_NAME: regression_metrics(test_actual, test["lag_24h_kwh"].to_numpy()),
        selected_name: regression_metrics(test_actual, test_prediction),
    }

    report: dict[str, Any] = {
        "task": "one-hour-ahead solar PV generation forecasting",
        "target": TARGET_COLUMN,
        "target_unit": "kWh per one-hour interval",
        "seed": seed,
        "row_counts": {
            "train": len(train),
            "validation": len(validation),
            "development_after_refit": len(development),
            "test": len(test),
        },
        "time_ranges_utc": {
            "train_start": train[TIMESTAMP_COLUMN].iloc[0].isoformat(),
            "train_end": train[TIMESTAMP_COLUMN].iloc[-1].isoformat(),
            "validation_start": validation[TIMESTAMP_COLUMN].iloc[0].isoformat(),
            "validation_end": validation[TIMESTAMP_COLUMN].iloc[-1].isoformat(),
            "test_start": test[TIMESTAMP_COLUMN].iloc[0].isoformat(),
            "test_end": test[TIMESTAMP_COLUMN].iloc[-1].isoformat(),
        },
        "validation_metrics": validation_reports,
        "test_metrics": test_reports,
        "selected_model": selected_name,
        "selection_policy": (
            "Lowest validation MAE; the held-out test set is not used for selection."
        ),
        "baseline": BASELINE_NAME,
        "warning": (
            "Synthetic data only. Scores demonstrate workflow behavior and are not evidence "
            "of production forecasting accuracy."
        ),
    }

    output = Path(artifacts_dir)
    output.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "format_version": 1,
            "feature_columns": FEATURE_COLUMNS,
            "target_column": TARGET_COLUMN,
            "selected_model_name": selected_name,
            "model": selected_model,
            "seed": seed,
        },
        output / "model_bundle.joblib",
    )
    (output / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def load_bundle(path: str | Path) -> dict[str, Any]:
    """Load a trusted model artifact and validate its schema."""
    bundle = joblib.load(Path(path))
    if (
        not isinstance(bundle, dict)
        or bundle.get("format_version") != 1
        or bundle.get("feature_columns") != FEATURE_COLUMNS
        or bundle.get("target_column") != TARGET_COLUMN
        or bundle.get("selected_model_name") not in {"hist_gradient_boosting", "random_forest"}
        or "model" not in bundle
    ):
        raise ValueError("model bundle schema is invalid")
    return bundle


def predict_frame(frame: pd.DataFrame, bundle: dict[str, Any]) -> pd.DataFrame:
    """Score a validated frame and include the seasonal-naive comparator."""
    frame = validate_frame(frame, require_target=TARGET_COLUMN in frame.columns)
    result = pd.DataFrame(
        {
            TIMESTAMP_COLUMN: frame[TIMESTAMP_COLUMN],
            "baseline_prediction_kwh": frame["lag_24h_kwh"].to_numpy(),
            "predicted_generation_kwh": np.clip(
                bundle["model"].predict(frame[FEATURE_COLUMNS]), 0.0, None
            ),
        }
    )
    if TARGET_COLUMN in frame.columns:
        result["actual_generation_kwh"] = frame[TARGET_COLUMN].to_numpy()
        result["absolute_error_kwh"] = np.abs(
            result["actual_generation_kwh"] - result["predicted_generation_kwh"]
        )
    return result
