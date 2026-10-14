# Machine Failure Early-Warning

A reproducible machine-learning portfolio project that predicts whether an industrial machine will fail within its next 12 operating hours. It includes synthetic telemetry generation, machine-level train/validation/test separation, a logistic regression classifier, a rule-based baseline, validation-only threshold selection, and held-out evaluation.

> The included data is synthetic. Metrics demonstrate the workflow and are not evidence of performance in a real factory.

## Quick start

Requires Python 3.11 or later. Runtime uses only the Python standard library.

```bash
python -m maintenance_ml.cli --output reports
python -m unittest discover -s tests -v
```

The CLI writes `reports/metrics.json` and `reports/predictions.csv`. Run in Docker with:

```bash
docker build -t machine-failure-early-warning .
docker run --rm -v "$PWD/reports:/app/reports" machine-failure-early-warning
```

## Problem and evaluation

Each snapshot contains vibration, temperature, pressure, current, and recent vibration trend. The target is 1 when a failure occurs within 12 operating hours. Positive cases are rare by design. Degradation increases sensor readings while adding noise and machine-specific operating offsets. This is a convenient reproducible benchmark, not a physically validated simulator.

Machines, rather than rows, are assigned to train, validation, and test partitions (60/20/20), preventing snapshots from a machine crossing partition boundaries. Scaling is fitted on training machines only. Validation data selects the alert threshold to maximize F1; test data evaluates that frozen threshold. The baseline is a transparent vibration rule.

Reported metrics include precision, recall, F1, PR-AUC (average precision), ROC-AUC, confusion counts, and alert rate. PR-AUC helps assess performance when positives are uncommon. The classifier is L2-regularized logistic regression trained with batch gradient descent.

For a real deployment, replace synthetic data with representative historical data and add time-aware backtesting, validated labels and horizons, cost-sensitive alert policies, drift monitoring, and human review.

## Layout

`maintenance_ml/` contains generation, model, metrics, and pipeline code; `tests/` contains deterministic unit and integration coverage; `.github/workflows/ci.yml` runs tests and a CLI smoke evaluation; `Dockerfile` builds a small non-root container.

## Reproducibility

Data generation and split assignment use explicit seeds (default 42). Data is generated in memory to keep the repository compact. MIT licensed; see [LICENSE](LICENSE).
