"""Synthetic data generation and strict dataset validation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "hour_sin",
    "hour_cos",
    "day_of_year_sin",
    "day_of_year_cos",
    "clear_sky_irradiance_wm2",
    "cloud_cover_forecast",
    "temperature_forecast_c",
    "humidity_forecast_pct",
    "lag_24h_kwh",
    "lag_168h_kwh",
]
TARGET_COLUMN = "pv_generation_kwh"
TIMESTAMP_COLUMN = "timestamp"
REQUIRED_COLUMNS = [TIMESTAMP_COLUMN, *FEATURE_COLUMNS]


def generate_dataset(
    days: int = 730,
    seed: int = 42,
    start: str = "2023-01-01T00:00:00Z",
) -> pd.DataFrame:
    """Generate deterministic, physics-inspired hourly PV observations.

    Weather inputs are synthetic forecast-time features. Lagged generation is available
    at each forecast origin, so the task represents rolling one-hour-ahead prediction.
    The generated data is for engineering demonstrations, not real-world model claims.
    """
    if days < 30:
        raise ValueError("days must be at least 30")

    rng = np.random.default_rng(seed)
    timestamps = pd.date_range(start=start, periods=days * 24, freq="h")
    hour = timestamps.hour.to_numpy(dtype=float)
    day_of_year = timestamps.dayofyear.to_numpy(dtype=float)

    hour_angle = 2.0 * np.pi * hour / 24.0
    year_angle = 2.0 * np.pi * (day_of_year - 172.0) / 365.25
    daylight_curve = np.clip(np.sin(np.pi * (hour - 6.0) / 12.0), 0.0, None)
    seasonal_factor = 0.45 + 0.55 * (0.5 + 0.5 * np.cos(year_angle))
    clear_sky = 950.0 * seasonal_factor * daylight_curve

    cloud_wave = 0.12 * np.sin(2.0 * np.pi * np.arange(len(timestamps)) / 41.0)
    cloud_cover = np.clip(rng.beta(2.2, 2.2, len(timestamps)) + cloud_wave, 0.0, 1.0)
    temperature = (
        10.0
        + 10.0 * np.cos(year_angle)
        + 5.0 * np.sin(hour_angle - np.pi / 2.0)
        + rng.normal(0.0, 2.0, len(timestamps))
    )
    humidity = np.clip(
        62.0 - 18.0 * daylight_curve + 13.0 * cloud_cover + rng.normal(0.0, 5.0, len(timestamps)),
        15.0,
        100.0,
    )

    cloud_transmission = np.clip(1.0 - 0.78 * cloud_cover, 0.08, 1.0)
    temperature_efficiency = np.clip(1.0 - 0.0035 * (temperature - 25.0), 0.85, 1.1)
    noise = rng.normal(0.0, 0.055, len(timestamps)) * (clear_sky > 0)
    generation = np.clip(
        5.0 * clear_sky / 1000.0 * cloud_transmission * temperature_efficiency + noise,
        0.0,
        5.5,
    )

    frame = pd.DataFrame(
        {
            TIMESTAMP_COLUMN: timestamps,
            "hour_sin": np.sin(hour_angle),
            "hour_cos": np.cos(hour_angle),
            "day_of_year_sin": np.sin(year_angle),
            "day_of_year_cos": np.cos(year_angle),
            "clear_sky_irradiance_wm2": clear_sky,
            "cloud_cover_forecast": cloud_cover,
            "temperature_forecast_c": temperature,
            "humidity_forecast_pct": humidity,
            TARGET_COLUMN: generation,
        }
    )
    frame["lag_24h_kwh"] = frame[TARGET_COLUMN].shift(24)
    frame["lag_168h_kwh"] = frame[TARGET_COLUMN].shift(168)
    frame = frame.dropna().reset_index(drop=True)
    return frame[[TIMESTAMP_COLUMN, *FEATURE_COLUMNS, TARGET_COLUMN]]


def validate_frame(frame: pd.DataFrame, require_target: bool = True) -> pd.DataFrame:
    """Validate schema, timestamp ordering, and finite numeric values."""
    missing = sorted(set(REQUIRED_COLUMNS) - set(frame.columns))
    if require_target and TARGET_COLUMN not in frame.columns:
        missing.append(TARGET_COLUMN)
    if missing:
        raise ValueError(f"missing required columns: {', '.join(sorted(set(missing)))}")

    columns = [TIMESTAMP_COLUMN, *FEATURE_COLUMNS]
    if require_target:
        columns.append(TARGET_COLUMN)
    data = frame[columns].copy()
    data[TIMESTAMP_COLUMN] = pd.to_datetime(data[TIMESTAMP_COLUMN], utc=True, errors="coerce")
    if data[TIMESTAMP_COLUMN].isna().any():
        raise ValueError("timestamp contains invalid values")
    if data[TIMESTAMP_COLUMN].duplicated().any():
        raise ValueError("timestamp values must be unique")
    if not data[TIMESTAMP_COLUMN].is_monotonic_increasing:
        raise ValueError("timestamp values must be sorted in ascending order")

    for column in [*FEATURE_COLUMNS, *([TARGET_COLUMN] if require_target else [])]:
        data[column] = pd.to_numeric(data[column], errors="coerce")
        values = data[column].to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError(f"{column} must contain finite numeric values")

    cloud_cover = data["cloud_cover_forecast"]
    if (cloud_cover < 0).any() or (cloud_cover > 1).any():
        raise ValueError("cloud_cover_forecast must be between 0 and 1")
    humidity = data["humidity_forecast_pct"]
    if (humidity < 0).any() or (humidity > 100).any():
        raise ValueError("humidity_forecast_pct must be between 0 and 100")
    if (data["clear_sky_irradiance_wm2"] < 0).any():
        raise ValueError("clear_sky_irradiance_wm2 must be non-negative")
    if (data["lag_24h_kwh"] < 0).any() or (data["lag_168h_kwh"] < 0).any():
        raise ValueError("lagged generation values must be non-negative")
    if require_target:
        target = data[TARGET_COLUMN]
        if (target < 0).any() or (target > 5.5).any():
            raise ValueError("pv_generation_kwh must be between 0 and 5.5")

    return data


def load_dataset(path: str | Path, require_target: bool = True) -> pd.DataFrame:
    """Read a CSV file and validate its contents."""
    return validate_frame(pd.read_csv(path), require_target=require_target)
