CREATE TABLE IF NOT EXISTS deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_hash CHAR(64) NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
    status TEXT NOT NULL CHECK (status IN ('queued','in_flight','retrying','delivered','dead_letter')),
    attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    last_http_status INTEGER CHECK (last_http_status BETWEEN 100 AND 599),
    last_error TEXT NOT NULL DEFAULT '',
    next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    lease_token UUID,
    lease_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    delivered_at TIMESTAMPTZ,
    UNIQUE (target_id, idempotency_key),
    CHECK (
      (status = 'in_flight' AND lease_token IS NOT NULL AND lease_until IS NOT NULL)
      OR (status <> 'in_flight' AND lease_token IS NULL AND lease_until IS NULL)
    ),
    CHECK ((status = 'delivered') = (delivered_at IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS deliveries_ready_idx ON deliveries(next_attempt_at, created_at) WHERE status IN ('queued','retrying');
CREATE INDEX IF NOT EXISTS deliveries_lease_idx ON deliveries(lease_until) WHERE status = 'in_flight';
CREATE INDEX IF NOT EXISTS deliveries_dead_letter_idx ON deliveries(created_at) WHERE status = 'dead_letter';
