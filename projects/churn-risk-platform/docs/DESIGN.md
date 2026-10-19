# Design notes

## Problem and decision boundary

The service ranks **risk of voluntary customer churn**, so a retention team can review a manageable queue. It must not automatically change prices, cancel accounts, or make decisions with legal/financial effect. `requires_review` is an operational routing signal, not a decision about a customer.

## Data contract

| Field | Meaning | Validation |
|---|---|---|
| `tenure_months` | completed subscription months | 0–600 |
| `monthly_charge` | current recurring charge | non-negative |
| `support_tickets_90d` | count in trailing 90 days | non-negative |
| `login_days_30d` | active days in trailing 30 days | 0–31 |
| `contract_type` | subscription commitment | controlled vocabulary |
| `payment_method` | active payment rail | controlled vocabulary |
| `autopay_enabled` | automatic billing flag | boolean |

Training labels must be built from a dated churn definition with a future observation window. Features must only contain values available before the prediction timestamp.

## Reliability and operations

* The API returns HTTP 503 until an artifact exists rather than scoring with an untrained model.
* FastAPI validates input; the Java client uses connection/read timeouts and rejects non-2xx results.
* Persist model versions and validation metrics alongside every artifact. Ship immutable artifacts, preferably from an object store, and set `MODEL_PATH` per deployment.
* Track request rate, latency, 4xx/5xx responses, prediction distribution, missingness, and feature drift. Recalibrate after a monitored champion/challenger evaluation.

## Security and privacy

Use TLS and service-to-service authentication in production. Limit logs to request IDs and model versions; do not log customer records. Apply retention policies and access controls to source data, artifacts, and review queues. Assess bias across permitted, privacy-reviewed cohorts before operational use.

## Deployment outline

1. CI runs `pytest` and static/dependency checks.
2. A scheduled, versioned training job validates schema and compares candidate metrics with the current model.
3. A reviewer approves a candidate, records its training period, and publishes the artifact.
4. Deploy the Python API behind a reverse proxy. Configure Java callers with the service base URL and credentials.
