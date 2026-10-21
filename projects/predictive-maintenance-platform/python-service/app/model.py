from pathlib import Path
from typing import Any
import joblib

FEATURES = ["asset_type", "operating_hours", "mean_vibration_mm_s", "temperature_c", "pressure_bar", "starts_24h", "lubricant_age_days"]


def load_bundle(path: str | Path) -> dict[str, Any]:
    bundle = joblib.load(path)
    required = {"pipeline", "threshold", "model_version", "metrics"}
    missing = required.difference(bundle)
    if missing:
        raise ValueError(f"Invalid model artifact; missing keys: {sorted(missing)}")
    return bundle
