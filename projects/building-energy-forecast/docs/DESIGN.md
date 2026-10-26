# Design notes

## Scope

The service forecasts hourly electricity demand to aid energy planning. It is advisory only; it must not directly control HVAC, life-safety, or electrical equipment.

## Data and evaluation

Training rows need a consistent meter timestamp, weather observation, occupancy estimate, and previously observed load. Time-sort production data before holdout evaluation to avoid future leakage. Monitor MAE/RMSE by building, hour, and season; retrain only after evaluating a time-based candidate against the deployed version.

## Operations

Reject implausible inputs at the API boundary and return 503 if no verified model exists. Use TLS, service authentication, request IDs, and least-privilege access to meter data. Track latency, error rate, missingness, feature drift, and forecast residuals. The Java caller uses finite timeouts; production callers should add retries and circuit breaking consistent with the building network.
