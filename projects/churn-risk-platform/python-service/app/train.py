import argparse
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from app.model import FEATURES


def synthetic_data(rows: int = 2000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    tenure = rng.integers(0, 73, rows)
    charge = rng.normal(72, 24, rows).clip(15, 180)
    tickets = rng.poisson(1.8, rows)
    logins = rng.integers(0, 31, rows)
    contract = rng.choice(["month_to_month", "one_year", "two_year"], rows, p=[.56, .27, .17])
    payment = rng.choice(["card", "bank_transfer", "invoice"], rows, p=[.50, .36, .14])
    autopay = rng.choice([True, False], rows, p=[.62, .38])
    logit = -0.8 + 1.25 * (contract == "month_to_month") + .55 * (payment == "invoice") + .7 * (~autopay) + .22 * tickets - .035 * tenure - .07 * logins + .008 * (charge - 70)
    probability = 1 / (1 + np.exp(-logit))
    churned = rng.binomial(1, probability)
    return pd.DataFrame({"customer_id": [f"C{i:05}" for i in range(rows)], "tenure_months": tenure, "monthly_charge": charge.round(2), "support_tickets_90d": tickets, "login_days_30d": logins, "contract_type": contract, "payment_method": payment, "autopay_enabled": autopay, "churned": churned})


def select_threshold(y_true: pd.Series, probabilities: np.ndarray) -> float:
    candidates = np.arange(.20, .81, .01)
    return float(max(candidates, key=lambda t: f1_score(y_true, probabilities >= t)))


def train(frame: pd.DataFrame) -> tuple[dict, dict]:
    X_train, X_valid, y_train, y_valid = train_test_split(frame[FEATURES], frame["churned"], test_size=.2, random_state=42, stratify=frame["churned"])
    numeric = ["tenure_months", "monthly_charge", "support_tickets_90d", "login_days_30d"]
    categorical = ["contract_type", "payment_method", "autopay_enabled"]
    pipeline = Pipeline([("prepare", ColumnTransformer([("numeric", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric), ("categorical", Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical)])), ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42))])
    pipeline.fit(X_train, y_train)
    probabilities = pipeline.predict_proba(X_valid)[:, 1]
    threshold = select_threshold(y_valid, probabilities)
    metrics = {"validation_auc": round(float(roc_auc_score(y_valid, probabilities)), 4), "validation_f1": round(float(f1_score(y_valid, probabilities >= threshold)), 4), "validation_rows": len(y_valid)}
    return {"pipeline": pipeline, "threshold": threshold, "model_version": "2026.10.19", "features": FEATURES, "metrics": metrics}, metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="CSV with churned label")
    parser.add_argument("--generate-synthetic", action="store_true")
    parser.add_argument("--output", default="artifacts/churn_model.joblib")
    args = parser.parse_args()
    if bool(args.input) == args.generate_synthetic:
        parser.error("Choose exactly one of --input or --generate-synthetic")
    data = synthetic_data() if args.generate_synthetic else pd.read_csv(args.input)
    bundle, metrics = train(data)
    destination = Path(args.output); destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, destination)
    print(f"saved={destination} metrics={metrics}")


if __name__ == "__main__":
    main()
