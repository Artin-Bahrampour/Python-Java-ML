# Security Notes and Threat Model

## Assets and trust boundaries

Assets include queued event payloads, signing secrets, delivery state, and the release decisions made from delivery status. API callers are untrusted; the target registry and deployment environment are trusted administrative inputs; downstream endpoints are external dependencies.

## Controls in this implementation

- Target IDs, not URLs, are accepted from API callers. URLs and signing secrets are loaded from a trusted configuration file and environment variables. The image default target file uses HTTPS; only Compose mounts the separate `targets.local.json` file for its development receiver.
- HTTPS is required for configured targets by default. HTTP requires the explicit `ALLOW_INSECURE_TARGETS=true` switch, intended only for local Compose development.
- Configured URLs with credentials, query strings, fragments, missing hosts, or IP literals in secure mode are rejected.
- Redirects are not followed, avoiding a target redirect from silently changing the destination.
- The HTTP client has connection/request timeouts, TLS 1.2 minimum, bounded connection pools, and no environment-proxy inheritance.
- Request bodies and target response bodies are bounded. Event payloads are never written to application logs.
- Webhook signatures use HMAC-SHA256 over `timestamp + newline + event ID + newline + event type + newline + attempt + newline + exact body`. The receiver fixture checks signatures and a five-minute timestamp tolerance. Production consumers must verify signatures and maintain replay/deduplication state.
- Signing secrets must be at least 32 bytes and are never included in API responses or logs.
- PostgreSQL uses parameterized queries; JSON payloads are stored as JSONB; idempotency is enforced by a database unique constraint.
- Docker runtime uses a non-root distroless image. CI has read-only repository permissions.

## Residual risks / deployment requirements

- The sample Compose database credentials and local secret are for development only. Use a secret manager, unique high-entropy secrets, and TLS to PostgreSQL in production.
- Target configuration is privileged. Apply outbound network policy/egress filtering to prevent access to cloud metadata services and internal control planes. DNS rebinding and private DNS destinations cannot be fully prevented by startup URL syntax checks alone.
- The API currently has no built-in user authentication, authorization, tenant isolation, or rate limiting. Do not expose it directly to the public internet. Restrict `/metrics` and readiness endpoints to trusted monitoring/network paths in production.
- Payloads are retained in PostgreSQL. Define retention, encryption-at-rest, access logging, and data minimization policies based on the event data you process.
- At-least-once delivery can produce duplicates. Consumers must be idempotent; signature freshness alone is not an event-deduplication strategy.
- A compromised worker can send configured payloads to configured targets. Restrict database and secret access to the minimum required services.
