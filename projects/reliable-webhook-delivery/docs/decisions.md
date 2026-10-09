# Engineering Decision Records

## ADR-001: PostgreSQL is both the durable queue and delivery ledger

**Decision:** Store queue state and delivery history in PostgreSQL rather than introducing a broker and a second persistence system.

**Context:** The project needs durable acceptance, uniqueness for idempotency, transactional claims, recoverable leases, and queryable failure state.

**Trade-offs:** PostgreSQL can become the throughput bottleneck at very high event volume, and table/index maintenance must be planned. The current workload is appropriate for a transactional queue. If throughput outgrows this design, preserve the idempotency ledger and move dispatch to a broker through an outbox-based migration rather than simply dual-writing.

## ADR-002: At-least-once delivery is explicit

**Decision:** Use lease recovery and retry rather than claiming exactly-once delivery.

**Context:** The process can crash after the receiver commits an event but before the worker records success. No local database transaction can atomically commit with an arbitrary remote HTTP server.

**Consequences:** Consumers must verify signatures and deduplicate by stable `X-Event-ID`. Delivery IDs are stable across retries. An operator replay feature must preserve an audit trail.

## ADR-003: Targets are configuration, not caller-provided URLs

**Decision:** API requests name a configured target ID; destination URLs and signing secrets are resolved at startup.

**Context:** Accepting arbitrary URLs creates an SSRF surface and lets callers redirect signed event data to attacker-controlled destinations.

**Consequences:** Adding a destination is an operational configuration change. Secure mode requires HTTPS and rejects IP-literal destinations; production network egress rules remain necessary because DNS and private routing cannot be secured by URL parsing alone.
