from pathlib import Path
from typing import Any
import joblib


FEATURES = ["tenure_months", "monthly_charge", "support_tickets_90d", "login_days_30d", "contract_type", "payment_method", "autopay_enabled"]


def load_bundle(path: str | Path) -> dict[str, Any]:
    bundle = joblib.load(path)
    required = {"pipeline", "threshold", "model_version"}
    missing = required.difference(bundle)
    if missing:
        raise ValueError(f"Invalid model artifact; missing: {sorted(missing)}")
    return bundle
