# HTTP API Contract

All request and response bodies use UTF-8 JSON. The API does not include authentication; deploy it behind a trusted gateway until an authentication/authorization layer is added.

## `POST /v1/deliveries`

Headers:

- `Content-Type: application/json`
- `Idempotency-Key: <1-200 printable ASCII characters>`

Body:

```json
{
  "target_id": "local-receiver",
  "event_type": "invoice.paid",
  "payload": { "invoice_id": "inv_123", "amount_minor": 129900, "currency": "NOK" }
}
```

`payload` must be a JSON object no larger than 256 KiB. Event types use lowercase dotted notation. The request is accepted only when `target_id` is configured.

Responses:

- `202 Accepted`: a new durable delivery was created.
- `200 OK`: the same target/key/request was submitted before; the original record is returned.
- `400 Bad Request`: invalid JSON, fields, key, event type, or payload.
- `409 Conflict`: the key already exists for this target but the normalized request differs.
- `413 Payload Too Large`: request body exceeds the API limit.
- `415 Unsupported Media Type`: content type is not JSON.
- `500 Internal Server Error`: unexpected persistence failure.

## `GET /v1/deliveries/{id}`

Returns delivery metadata including `status`, `attempts`, `last_http_status`, `last_error`, `next_attempt_at`, and `delivered_at`. The event payload is intentionally not returned by the status endpoint. `400` means the ID is not a valid UUID; `404` means a valid ID does not exist.

## Webhook headers

Each outbound request includes `X-Event-ID`, `X-Event-Type`, `X-Delivery-Attempt`, `X-Webhook-Timestamp`, and `X-Webhook-Signature`. The signature is `t=<unix-seconds>,v1=<lowercase-hex-HMAC-SHA256>` over the UTF-8 bytes of `<timestamp>\n<event-id>\n<event-type>\n<attempt>\n<exact-request-body>`. Verify against the exact bytes received, enforce a short timestamp tolerance, compare signatures in constant time, and deduplicate on `X-Event-ID`.
