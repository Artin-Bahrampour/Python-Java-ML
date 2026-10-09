# Reliable Webhook Delivery

A durable, PostgreSQL-backed outbound webhook delivery service built in Go. It is designed for systems that must notify downstream services without coupling business requests to downstream uptime.

## Why this matters

Synchronous webhook calls can lose events during outages or tie API latency to the slowest consumer. This service persists events first, dispatches them asynchronously, retries transient failures, signs requests, and exposes terminal failures for operational investigation.

## Capabilities

- Durable PostgreSQL queue with multiple-worker coordination via `FOR UPDATE SKIP LOCKED`.
- Idempotent submission using a required `Idempotency-Key` and database uniqueness constraint.
- Canonical JSON hashing so whitespace/key-order changes do not create false idempotency conflicts.
- Lease-based worker claims, crash recovery, and lease-token guarded completion.
- Capped exponential full-jitter retries, `Retry-After` support, and immediate dead-lettering for permanent 4xx responses.
- HMAC-SHA256 request signatures and a local receiver fixture that verifies signatures.
- Bounded request/response bodies, strict request decoding, timeout limits, no redirects, and HTTPS-by-default target configuration.
- JSON structured logs, request IDs, readiness/liveness endpoints, Prometheus metrics, and graceful shutdown.
- Embedded versioned SQL migrations, Docker multi-stage build, Compose environment, unit tests, PostgreSQL integration tests, and CI.

## Architecture

See [Architecture](docs/architecture.md), [API contract](docs/api.md), [Security / threat model](docs/security.md), and [Operations runbook](docs/operations.md).

```text
Producer -> HTTP API -> PostgreSQL durable queue
                            |
                    leased worker pool
                            |
              configured target + HMAC signature
                            |
                    downstream endpoint
```

## Requirements

- Go 1.27+
- PostgreSQL 16+ for local development
- Docker Engine and Compose v2 for the full local stack

## Run locally with Compose

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
```

The stack starts PostgreSQL, the API on `localhost:8080`, a background worker, and a local signature-verifying receiver. Compose mounts `config/targets.local.json` for this development-only receiver and enables plain HTTP solely inside the Compose network. The image default `config/targets.json` is HTTPS-only and should be replaced with your trusted production destinations and secret environment variables.

Submit the sample event:

```bash
curl -i http://localhost:8080/v1/deliveries   -H 'Content-Type: application/json'   -H 'Idempotency-Key: invoice-inv_2026_000184-paid-v1'   --data @examples/event.json
```

The API returns `202 Accepted` and a delivery ID. Inspect its status:

```bash
curl -s http://localhost:8080/v1/deliveries/<delivery-id> | python -m json.tool
```

See the full walkthrough and troubleshooting commands in [Operations](docs/operations.md).

## Run tests

```bash
gofmt -w $(find . -name '*.go')
go mod tidy
go vet ./...
go test -race ./...
```

The PostgreSQL integration test is skipped unless `TEST_DATABASE_URL` is set. Example:

```bash
TEST_DATABASE_URL='postgres://webhook:webhook@localhost:5432/webhooks?sslmode=disable' go test -race ./internal/store -count=1
```

## API summary

- `POST /v1/deliveries` — persist a delivery (requires `Idempotency-Key`).
- `GET /v1/deliveries/{id}` — inspect delivery status.
- `GET /healthz` — liveness.
- `GET /readyz` — PostgreSQL readiness.
- `GET /metrics` — Prometheus text format (API on port 8080; worker on its internal port 9090).

## Delivery guarantees and limitations

Delivery is **at least once**, not exactly once. A downstream service may receive the same event more than once if it accepts a request and the worker crashes before committing success. Consumers should deduplicate by `X-Event-ID`. Permanent failures and exhausted retries enter `dead_letter`; a replay/operator UI is intentionally out of scope.

The current API has no built-in authentication, authorization, tenant isolation, or rate limiting. Do not expose it directly to the public internet. See [Security](docs/security.md) for required production controls and residual risks.

## Technology choices

- **Go**: compact statically linked services, predictable concurrency, and simple operational packaging.
- **PostgreSQL**: durable queue state, transactional claims, uniqueness guarantees, and queryable delivery history without introducing a second datastore.
- **Standard-library HTTP**: small dependency surface and explicit request/timeout behavior.
- **JSON + HMAC-SHA256**: interoperable event envelope and verifiable message integrity.
- **Docker/distroless + GitHub Actions**: reproducible builds, non-root runtime, automated tests, and container build verification.

## License

MIT. See [LICENSE](LICENSE).
