from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

FEATURES = [
    "tenure_months",
    "monthly_spend",
    "support_tickets_90d",
    "late_payments_12m",
    "usage_days_30d",
    "plan_type",
    "contract_type",
    "autopay",
]
TARGET = "churned"
REQUIRED = FEATURES + [TARGET]


def generate_customers(rows: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Create deterministic synthetic customer records for repeatable experiments."""
    if rows < 100:
        raise ValueError("rows must be at least 100")
    rng = np.random.default_rng(seed)
    tenure = rng.integers(1, 73, rows)
    spend = np.clip(rng.normal(58, 22, rows), 10, 220).round(2)
    tickets = np.clip(rng.poisson(1.2, rows), 0, 12)
    late = np.clip(rng.poisson(0.55, rows), 0, 8)
    usage = np.clip(rng.normal(18, 7, rows), 0, 30).round().astype(int)
    plan = rng.choice(["basic", "standard", "premium"], rows, p=[0.42, 0.40, 0.18])
    contract = rng.choice(["monthly", "annual", "two_year"], rows, p=[0.52, 0.33, 0.15])
    autopay = rng.binomial(1, 0.62, rows)
    logit = (
        -1.35
        - 0.022 * tenure
        + 0.12 * tickets
        + 0.34 * late
        - 0.055 * usage
        + 0.9 * (contract == "monthly")
        - 0.7 * (contract == "two_year")
        - 0.45 * autopay
        + 0.003 * (spend - 55)
        + 0.15 * (plan == "basic")
    )
    probability = 1 / (1 + np.exp(-logit))
    churn = rng.binomial(1, probability)
    return pd.DataFrame(
        {
            "tenure_months": tenure,
            "monthly_spend": spend,
            "support_tickets_90d": tickets,
            "late_payments_12m": late,
            "usage_days_30d": usage,
            "plan_type": plan,
            "contract_type": contract,
            "autopay": autopay,
            "churned": churn,
        }
    )


def validate_frame(frame: pd.DataFrame, require_target: bool = True) -> pd.DataFrame:
    required = REQUIRED if require_target else FEATURES
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")
    data = frame[required].copy()
    for col in ["tenure_months", "support_tickets_90d", "late_payments_12m", "usage_days_30d"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
        vals = data[col].to_numpy(dtype=float)
        if (
            not np.isfinite(vals).all()
            or (vals < 0).any()
            or not np.equal(vals, np.floor(vals)).all()
        ):
            raise ValueError(f"{col} must contain non-negative integers")
    data["monthly_spend"] = pd.to_numeric(data["monthly_spend"], errors="coerce")
    if (
        not np.isfinite(data["monthly_spend"].to_numpy(dtype=float)).all()
        or (data["monthly_spend"] <= 0).any()
    ):
        raise ValueError("monthly_spend must be finite and positive")
    if not data["usage_days_30d"].between(0, 30).all():
        raise ValueError("usage_days_30d must be between 0 and 30")
    for col, allowed in {
        "plan_type": {"basic", "standard", "premium"},
        "contract_type": {"monthly", "annual", "two_year"},
    }.items():
        data[col] = data[col].astype("string").str.strip()
        if data[col].isna().any() or not data[col].isin(allowed).all():
            raise ValueError(f"{col} contains unsupported values")
    data["autopay"] = pd.to_numeric(data["autopay"], errors="coerce")
    if data["autopay"].isna().any() or not data["autopay"].isin([0, 1]).all():
        raise ValueError("autopay must contain only 0 or 1")
    if require_target:
        data[TARGET] = pd.to_numeric(data[TARGET], errors="coerce")
        if (
            data[TARGET].isna().any()
            or not data[TARGET].isin([0, 1]).all()
            or data[TARGET].nunique() != 2
        ):
            raise ValueError("churned must contain both classes encoded as 0 or 1")
    for col in [
        "tenure_months",
        "support_tickets_90d",
        "late_payments_12m",
        "usage_days_30d",
        "autopay",
    ]:
        data[col] = data[col].astype(int)
    data["monthly_spend"] = data["monthly_spend"].astype(float)
    return data


def load_csv(path: str | Path, require_target: bool = True) -> pd.DataFrame:
    return validate_frame(pd.read_csv(path), require_target)
