"""Machine-level splitting and end-to-end benchmark evaluation."""

from __future__ import annotations

import random

from .data import FEATURES, generate_dataset
from .metrics import best_f1_threshold, classification_metrics
from .model import LogisticRegression, Standardizer


def evaluate(seed: int = 42) -> tuple[dict, list[dict]]:
    rows = generate_dataset(seed)
    machines = sorted({row.machine_id for row in rows})
    random.Random(seed).shuffle(machines)
    n_train, n_val = int(len(machines) * .6), int(len(machines) * .2)
    train_ids = set(machines[:n_train])
    val_ids = set(machines[n_train:n_train + n_val])
    test_ids = set(machines[n_train + n_val:])
    train = [r for r in rows if r.machine_id in train_ids]
    val = [r for r in rows if r.machine_id in val_ids]
    test = [r for r in rows if r.machine_id in test_ids]
    scaler = Standardizer().fit([r.values for r in train])
    model = LogisticRegression().fit(scaler.transform([r.values for r in train]),
                                     [r.label for r in train])
    val_scores = model.predict_proba(scaler.transform([r.values for r in val]))
    threshold = best_f1_threshold([r.label for r in val], val_scores)
    test_scores = model.predict_proba(scaler.transform([r.values for r in test]))
    labels = [r.label for r in test]
    learned = classification_metrics(labels, test_scores, threshold)
    baseline_scores = [float(r.values[0] >= 2.35) for r in test]
    baseline = classification_metrics(labels, baseline_scores, .5)
    metrics = {
        "project": "machine-failure-early-warning", "seed": seed,
        "feature_names": list(FEATURES),
        "split": {"train_machines": len(train_ids), "validation_machines": len(val_ids),
                  "test_machines": len(test_ids), "train_rows": len(train),
                  "validation_rows": len(val), "test_rows": len(test)},
        "positive_rate_test": sum(labels) / len(labels), "selected_threshold": threshold,
        "logistic_regression": learned, "vibration_rule_baseline": baseline,
    }
    predictions = [{"machine_id": r.machine_id, "hour": r.hour, "label": r.label,
                    "probability": score, "alert": int(score >= threshold)}
                   for r, score in zip(test, test_scores)]
    return metrics, predictions
