# Operations Guide

1. Validate schema and monitor missing/invalid values.
2. Record seed, data version, code revision, and metrics for every run.
3. Compare candidates with the baseline; do not use accuracy alone.
4. Review threshold trade-offs and calibration before using scores.
5. Keep model and metrics artifacts together; retain a previous model for rollback.
6. Once outcomes mature, monitor ROC-AUC, average precision, calibration, drift, and subgroup error rates.

This repository provides local batch scoring, not a deployed service or model registry. Treat `joblib` bundles as trusted artifacts and never load untrusted model files.
