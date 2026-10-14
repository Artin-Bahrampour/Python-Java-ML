from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from churn_ml.data import FEATURES, TARGET

NUMERIC = [
    "tenure_months",
    "monthly_spend",
    "support_tickets_90d",
    "late_payments_12m",
    "usage_days_30d",
    "autopay",
]
CATEGORICAL = ["plan_type", "contract_type"]


def preprocessor() -> ColumnTransformer:
    num = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    cat = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer([("numeric", num, NUMERIC), ("categorical", cat, CATEGORICAL)])


def build_models(seed: int = 42) -> dict[str, Pipeline]:
    return {
        "logistic_regression_baseline": Pipeline(
            [
                ("preprocessor", preprocessor()),
                (
                    "classifier",
                    LogisticRegression(max_iter=1000, class_weight="balanced", random_state=seed),
                ),
            ]
        ),
        "random_forest": Pipeline(
            [
                ("preprocessor", preprocessor()),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=250,
                        min_samples_leaf=3,
                        class_weight="balanced_subsample",
                        random_state=seed,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }


def evaluate(y_true: np.ndarray, prob: np.ndarray, threshold: float = 0.5) -> dict[str, Any]:
    if len(y_true) == 0 or len(y_true) != len(prob):
        raise ValueError("labels and probabilities must be non-empty and have equal lengths")
    if not np.isfinite(prob).all() or ((prob < 0) | (prob > 1)).any():
        raise ValueError("probabilities must be finite values between 0 and 1")
    pred = (prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    return {
        "roc_auc": float(roc_auc_score(y_true, prob)),
        "average_precision": float(average_precision_score(y_true, prob)),
        "precision": float(precision_score(y_true, pred, zero_division=0)),
        "recall": float(recall_score(y_true, pred, zero_division=0)),
        "f1": float(f1_score(y_true, pred, zero_division=0)),
        "brier_score": float(brier_score_loss(y_true, prob)),
        "threshold": threshold,
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "rows": int(len(y_true)),
    }


def train_and_evaluate(frame, artifacts_dir: str | Path, seed: int = 42) -> dict[str, Any]:
    out = Path(artifacts_dir)
    out.mkdir(parents=True, exist_ok=True)
    X = frame[FEATURES]
    y = frame[TARGET].astype(int)
    X_dev, X_test, y_dev, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_dev, y_dev, test_size=0.25, random_state=seed, stratify=y_dev
    )
    candidates = {}
    validation_reports = {}
    for name, model in build_models(seed).items():
        model.fit(X_train, y_train)
        validation_reports[name] = evaluate(y_val.to_numpy(), model.predict_proba(X_val)[:, 1])
        candidates[name] = model
    selected = max(validation_reports, key=lambda name: validation_reports[name]["roc_auc"])

    # Refit both candidates on the full development set; keep test data untouched until now.
    test_reports = {}
    final_models = {}
    for name, model in build_models(seed).items():
        model.fit(X_dev, y_dev)
        test_reports[name] = evaluate(y_test.to_numpy(), model.predict_proba(X_test)[:, 1])
        final_models[name] = model

    report = {
        "task": "binary customer churn classification",
        "seed": seed,
        "split": {
            "train_rows": len(X_train),
            "validation_rows": len(X_val),
            "development_rows": len(X_dev),
            "test_rows": len(X_test),
        },
        "class_balance": {
            "train_churn_rate": float(y_train.mean()),
            "validation_churn_rate": float(y_val.mean()),
            "test_churn_rate": float(y_test.mean()),
        },
        "validation_models": validation_reports,
        "test_models": test_reports,
        "selected_model": selected,
        "selection_metric": "validation ROC-AUC; held-out test set is not used for model selection",
        "warning": "Synthetic data only; metrics do not represent real-world performance.",
    }
    joblib.dump(
        {
            "format_version": 1,
            "feature_columns": FEATURES,
            "models": final_models,
            "selected_model": selected,
        },
        out / "model_bundle.joblib",
    )
    (out / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def load_bundle(path: str | Path) -> dict[str, Any]:
    bundle = joblib.load(Path(path))
    if (
        not isinstance(bundle, dict)
        or bundle.get("format_version") != 1
        or bundle.get("feature_columns") != FEATURES
        or bundle.get("selected_model") not in bundle.get("models", {})
    ):
        raise ValueError("model bundle schema is invalid")
    return bundle
