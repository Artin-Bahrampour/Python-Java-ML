# Operations

`POST /v1/triage` is an advisory prioritisation signal, not an automated rejection decision. Review threshold is selected to retain recall while requiring at least 45% training precision. Monitor input ranges, positive-review rate, latency and post-review precision. Retrain only with versioned, privacy-approved labels; evaluate by time-based holdout before promotion. The service exposes `/health` and `/metrics` for probes and monitoring.
