# Operations Runbook

## Local startup

Requirements: Docker Engine with Compose v2 and `curl`.

```bash
cp .env.example .env
# Keep the provided secret only for local development.
docker compose up --build -d
docker compose ps
```

The API is available on `http://localhost:8080`. The local receiver is intentionally not published to the host.

## Submit an event

```bash
curl -i http://localhost:8080/v1/deliveries   -H 'Content-Type: application/json'   -H 'Idempotency-Key: invoice-inv_2026_000184-paid-v1'   --data @examples/event.json
```

The sample file contains the request fields. Copy the returned `id`, then inspect the delivery:

```bash
curl -s http://localhost:8080/v1/deliveries/<delivery-id> | python -m json.tool
```

A quick `GET` may still show `queued` or `in_flight`; poll until `delivered` or `dead_letter`. Matching submissions with the same key return the original record. Change the payload but keep the key to see a `409` conflict.

## Useful commands

```bash
docker compose logs -f api worker receiver
docker compose exec postgres psql -U webhook -d webhooks -c "SELECT status, count(*) FROM deliveries GROUP BY status;"
curl -s http://localhost:8080/metrics
```

## Alerting suggestions

Alert on sustained growth in `dead_letter`, delivery age (oldest due row), repeated 5xx/429 responses, worker restarts, database connection exhaustion, and elevated retry counts. The API exposes its counters on `:8080/metrics`; the worker exposes delivery counters on its internal `:9090/metrics` endpoint. Scrape both processes separately and combine them in your monitoring system. For production, add queue-depth/oldest-age gauges from SQL and histograms for request and delivery latency.

## Recovery

Dead-letter records remain in PostgreSQL for investigation. This version deliberately does not expose a replay endpoint. To replay, build an audited operator workflow that verifies the cause, records who approved the replay, preserves the original event ID or creates a linked replay ID, and reuses the same signing policy. Do not manually reset rows in production without an audit trail.

## Shutdown and crash behavior

The API gracefully stops accepting new connections. The worker stops polling when its context is cancelled; an in-flight HTTP request is cancelled, leaving the lease to expire so another worker can recover it. Keep the lease longer than the request timeout plus a safety margin. Database migrations are embedded and applied at process startup.
