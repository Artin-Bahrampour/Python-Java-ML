import argparse
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from app.model import FEATURES


def synthetic_data(rows: int = 3000, seed: int = 73) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    asset_type = rng.choice(["centrifugal_pump", "positive_displacement_pump"], rows, p=[.72, .28])
    hours = rng.gamma(4, 1800, rows).clip(50, 30000)
    vibration = rng.normal(3.1, 1.2, rows).clip(.1, 12)
    temperature = rng.normal(68, 14, rows).clip(10, 160)
    pressure = rng.normal(8.5, 2.0, rows).clip(.2, 25)
    starts = rng.poisson(4, rows)
    lubricant_age = rng.gamma(3, 22, rows).clip(1, 365).astype(int)
    logit = -5.0 + .42 * vibration + .025 * (temperature - 65) + .012 * lubricant_age + .000055 * hours + .09 * starts + .35 * (asset_type == "positive_displacement_pump")
    risk = 1 / (1 + np.exp(-logit))
    failed = rng.binomial(1, risk)
    return pd.DataFrame({"asset_id": [f"PUMP-{i:05d}" for i in range(rows)], "asset_type": asset_type, "operating_hours": hours.round(1), "mean_vibration_mm_s": vibration.round(3), "temperature_c": temperature.round(2), "pressure_bar": pressure.round(2), "starts_24h": starts, "lubricant_age_days": lubricant_age, "failure_14d": failed})


def choose_threshold(y: pd.Series, probabilities: np.ndarray, precision_floor: float = .35) -> float:
    candidates = np.arange(.10, .91, .01)
    eligible = [t for t in candidates if precision_score(y, probabilities >= t, zero_division=0) >= precision_floor]
    pool = eligible or list(candidates)
    return float(max(pool, key=lambda t: recall_score(y, probabilities >= t, zero_division=0)))


def train(frame: pd.DataFrame) -> tuple[dict, dict]:
    X_train, X_valid, y_train, y_valid = train_test_split(frame[FEATURES], frame["failure_14d"], test_size=.2, random_state=73, stratify=frame["failure_14d"])
    numeric = FEATURES[1:]
    transformer = ColumnTransformer([("numbers", SimpleImputer(strategy="median"), numeric), ("asset", Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), ["asset_type"])])
    pipeline = Pipeline([("prepare", transformer), ("classifier", HistGradientBoostingClassifier(max_iter=180, learning_rate=.08, max_leaf_nodes=15, l2_regularization=.4, random_state=73))])
    pipeline.fit(X_train, y_train)
    probabilities = pipeline.predict_proba(X_valid)[:, 1]
    threshold = choose_threshold(y_valid, probabilities)
    metrics = {"validation_auc": round(float(roc_auc_score(y_valid, probabilities)), 4), "validation_average_precision": round(float(average_precision_score(y_valid, probabilities)), 4), "validation_recall": round(float(recall_score(y_valid, probabilities >= threshold)), 4), "validation_precision": round(float(precision_score(y_valid, probabilities >= threshold, zero_division=0)), 4), "validation_rows": len(y_valid)}
    return {"pipeline": pipeline, "threshold": threshold, "model_version": "2026.10.21", "features": FEATURES, "metrics": metrics}, metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="CSV containing failure_14d label")
    parser.add_argument("--generate-synthetic", action="store_true")
    parser.add_argument("--output", default="artifacts/maintenance_model.joblib")
    args = parser.parse_args()
    if bool(args.input) == args.generate_synthetic:
        parser.error("Choose exactly one of --input or --generate-synthetic")
    frame = synthetic_data() if args.generate_synthetic else pd.read_csv(args.input)
    bundle, metrics = train(frame)
    target = Path(args.output); target.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, target)
    print(f"saved={target} metrics={metrics}")


if __name__ == "__main__":
    main()
