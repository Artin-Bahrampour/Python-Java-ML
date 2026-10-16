# Solar PV Generation Forecasting

A reproducible machine-learning project for **one-hour-ahead solar photovoltaic (PV) generation forecasting**. It compares a seasonal-naive baseline with two tree-based regressors, uses chronological model selection, reports held-out test metrics, persists a model artifact, supports batch scoring, and provides a lightweight feature-drift report.

> **Data disclaimer:** The included data generator is synthetic and physics-inspired. This repository demonstrates engineering and evaluation practice; its metrics are not evidence of real-world forecast accuracy.

## Problem statement

PV operators need short-horizon generation estimates for planning, balancing, and operational awareness. This project estimates the energy generated during the next hourly interval using forecast-time weather features, solar geometry, and generation observations available from earlier intervals.

## Engineering highlights

- Deterministic, configurable synthetic hourly data with a documented schema.
- Strict schema, timestamp, numeric-range, and finite-value validation.
- Chronological train/validation/test partitions; no random time-series split.
- Seasonal-naive baseline using generation from the same hour on the previous day.
- Validation-MAE model selection between histogram gradient boosting and random forest.
- Final evaluation on a held-out test period that is not used for model selection.
- MAE, RMSE, and R² metrics with machine-readable reports.
- Versioned model-bundle schema, batch inference, and Population Stability Index (PSI) drift checks.
- Unit/integration tests, Ruff lint/format checks, Docker, and GitHub Actions CI.

## Architecture

```text
Synthetic hourly weather + solar geometry
                  |
                  v
       CSV schema validation
                  |
                  v
  Chronological train / validation / test
                  |
        +---------+----------+
        |                    |
        v                    v
 Seasonal-naive         Candidate models
 lag-24h baseline       HistGradientBoosting
                        RandomForest
        |                    |
        +------ validation MAE selection
                             |
                             v
               Refit on train + validation
                             |
                             v
                Held-out test evaluation
                             |
                +------------+-----------+
                |                        |
                v                        v
          Model bundle              Metrics JSON
                |
                v
          Batch predictions

Reference feature batch + current feature batch -> PSI drift report
```

## Technology choices

- **Python 3.11+** for the end-to-end ML workflow and CLI.
- **pandas / NumPy** for time-series generation, feature construction, and validation.
- **scikit-learn** for reproducible regressors and evaluation metrics.
- **joblib** for trusted local model-artifact persistence.
- **pytest / Ruff** for regression tests and code-quality checks.
- **Docker** for a non-root, minimal runtime image; **GitHub Actions** for automated checks.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"

pv-forecast generate --output data/generated/pv_hourly.csv --days 730 --seed 42
pv-forecast train --data data/generated/pv_hourly.csv --artifacts-dir artifacts --seed 42
pv-forecast evaluate --artifacts-dir artifacts
pv-forecast predict --data data/generated/pv_hourly.csv --artifacts-dir artifacts --output artifacts/predictions.csv
pv-forecast monitor --reference data/generated/pv_hourly.csv --current data/generated/pv_hourly.csv --output artifacts/drift-report.json

pytest
ruff check .
ruff format --check .
```

Equivalent Make targets are available; run `make` to see the target names in `Makefile`.

## Evaluation protocol

1. Sort records by timestamp.
2. Use the earliest 70% for training, the next 15% for validation, and the final 15% for testing.
3. Compare candidate models using validation MAE only.
4. Refit the selected model on the combined train and validation periods.
5. Evaluate the selected model and seasonal-naive baseline on the held-out test period.

MAE and RMSE are reported in kWh per one-hour interval. R² is included as a supplementary fit statistic. Do not compare results across random seeds or data-generation versions as if they were a production benchmark.

### Forecast-origin assumptions and leakage

The target at time `t` is predicted using synthetic weather forecasts and generation lags at `t-24h` and `t-168h`. These lag values are assumed to be observed by the time the forecast for `t` is made. This is a rolling one-hour-ahead setup, not a multi-day forecast generated once at the beginning of the test window. A production implementation must preserve this forecast-origin contract and use actual archived forecast vintages rather than realized future weather.

## Data dictionary

| Column | Meaning |
| --- | --- |
| `timestamp` | UTC timestamp of the hourly generation interval |
| `hour_sin`, `hour_cos` | Cyclical hour-of-day encoding |
| `day_of_year_sin`, `day_of_year_cos` | Cyclical annual-season encoding |
| `clear_sky_irradiance_wm2` | Synthetic clear-sky irradiance proxy |
| `cloud_cover_forecast` | Synthetic cloud-cover forecast in `[0, 1]` |
| `temperature_forecast_c` | Synthetic temperature forecast in Celsius |
| `humidity_forecast_pct` | Synthetic relative-humidity forecast in percent |
| `lag_24h_kwh` | Generation observed 24 hours before the target interval |
| `lag_168h_kwh` | Generation observed 168 hours before the target interval |
| `pv_generation_kwh` | Target: energy generated in the one-hour interval |

## Docker

```bash
docker build -t solar-pv-generation-forecasting .
docker run --rm solar-pv-generation-forecasting --help
```

The image runs as a non-root user, drops unnecessary capabilities in Compose, and does not bundle generated datasets or model artifacts.

## CI integration when nested in a portfolio monorepo

The workflow at `.github/workflows/ci.yml` works when this repository is used standalone. GitHub does **not** discover workflows nested under `projects/solar-pv-generation-forecasting/.github/workflows/` in a monorepo. When adding this folder to a portfolio repository, merge the relevant checks into the repository-root workflow and add `projects/solar-pv-generation-forecasting` to its project matrix. For this project, install dependencies with `pip install -e ".[dev]"` from that matrix working directory, then run `ruff check .`, `ruff format --check .`, and `pytest`. Preserve the existing projects' dependency-installation logic.

## Limitations and next steps

- Synthetic data does not capture real weather forecast errors, equipment outages, curtailment, degradation, or site-specific behavior.
- The lag features assume hourly observations are available at forecast time.
- PSI thresholds are heuristic alerting aids, not statistical significance tests or automatic rollback criteria.
- Production readiness would require real historical generation, archived weather forecast vintages, rolling-origin backtests across seasons, uncertainty intervals, site-level calibration, data-quality alerts, and monitored retraining.
