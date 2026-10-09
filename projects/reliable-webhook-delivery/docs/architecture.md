# Architecture and Delivery Semantics

## Problem

Internal systems often need to notify downstream services after a business event. Direct synchronous HTTP calls couple the producer to target availability and can lose notifications when the target is unavailable or the producer crashes. This service accepts events durably and delivers them asynchronously with bounded retries, idempotent submission, signed requests, and an inspectable dead-letter state.

## Components

- **HTTP API** validates submissions, enforces an idempotency key, canonicalizes JSON payloads, and persists the delivery before returning `202 Accepted`.
- **PostgreSQL** is the durable queue and source of truth. A unique `(target_id, idempotency_key)` constraint protects submission from duplicate retries.
- **Worker** claims one due delivery in a short transaction with `FOR UPDATE SKIP LOCKED`, increments its attempt count, and records a lease token and expiry. Network I/O happens after the transaction commits.
- **Target registry** is trusted startup configuration. Callers select a target ID; they cannot submit arbitrary destination URLs.
- **Receiver fixture** is a local-only signed-webhook sink for a reproducible end-to-end walkthrough.
- **Metrics and JSON logs** expose queue outcomes and operational context without logging event payloads or secrets.

## State machine

`queued -> in_flight -> delivered`

`in_flight -> retrying -> in_flight ...`

`in_flight -> dead_letter`

A lease makes work recoverable after a worker crashes. A new worker can reclaim an expired lease. Completion/failure updates require the lease token, preventing a stale worker from overwriting a newer attempt. A delivery may be sent more than once if a target accepts a request but the worker crashes before committing success. Therefore this is **at-least-once delivery**, not exactly-once delivery. Consumers should deduplicate using `X-Event-ID`.

## Retry policy

Network errors, timeouts, HTTP 408, 425, 429, and 5xx responses are retryable. Other non-2xx responses are treated as permanent failures and dead-lettered immediately. Retryable failures use capped exponential full-jitter backoff, respecting `Retry-After` up to the configured cap. Exhausted deliveries enter `dead_letter` and remain queryable for manual investigation/replay tooling.

## API

- `POST /v1/deliveries` — requires `Idempotency-Key`, JSON body `{ "target_id", "event_type", "payload" }`; returns `202` for a new delivery and `200` for a matching replay. Reusing the same key with a different normalized request returns `409`.
- `GET /v1/deliveries/{id}` — inspect state, attempt count, next attempt time, and final delivery time.
- `GET /healthz` — process liveness.
- `GET /readyz` — readiness including PostgreSQL connectivity.
- `GET /metrics` — Prometheus text exposition.

## Storage and concurrency

The queue uses PostgreSQL row locks with `SKIP LOCKED`, so multiple worker replicas can safely compete without a global in-memory lock. Lease expiry, retry scheduling, and completion timestamps use the PostgreSQL server clock to avoid worker-host clock skew. No transaction is held open while waiting on a downstream HTTP endpoint. A lease token is an optimistic ownership guard, not a distributed exactly-once primitive.

## Operational boundaries

The current release intentionally does not include a public target-registration API, replay UI, or tenant authorization. Target definitions and signing secrets are deployment configuration. Put the API behind an authenticated gateway, apply per-tenant quotas, and add an audited replay workflow before exposing it to untrusted external clients.
