# Operations Guide

## Local workflow

1. Install with `pip install -e ".[dev]"`.
2. Generate a fixed-seed dataset.
3. Train and inspect `artifacts/metrics.json`.
4. Score a batch and review the baseline and model predictions.
5. Compare reference and current feature batches using the PSI report.
6. Run tests and Ruff checks before publishing changes.

## Artifacts

- `model_bundle.joblib`: versioned bundle schema with feature list and selected estimator.
- `metrics.json`: split boundaries, validation metrics, test metrics, selected model, and synthetic-data warning.
- `predictions.csv`: timestamp, baseline prediction, model prediction, and actual/error columns when labels are available.
- `drift-report.json`: per-feature PSI values and heuristic drift flags.

Generated files live under `artifacts/` or `data/generated/` and are excluded from Git.

## Observability

The CLI emits a concise row-count/output-path message for data generation and scoring, writes structured JSON metrics, and provides a PSI report for feature-distribution review. In a real deployment, send metrics and logs to a central system and add alerting for missing batches, stale timestamps, excessive forecast error, and persistent drift.

PSI threshold 0.2 is a configurable heuristic. Review seasonal effects and feature-specific behavior before acting on an alert.

## Incident response

1. Pause automated promotion if data validation fails or a batch is incomplete.
2. Preserve input batch identifiers, model version, timestamps, and generated reports.
3. Compare current MAE/RMSE against the seasonal-naive baseline on newly labeled observations.
4. Investigate data-source changes, timestamp misalignment, forecast-vintage mismatch, and seasonal shift.
5. Revert to an approved previous model or baseline if an independently defined service-level threshold is breached.
6. Record the cause and validation evidence before resuming automated promotion.

The repository does not implement production deployment, paging, or automatic rollback.
