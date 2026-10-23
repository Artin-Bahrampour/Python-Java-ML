# Design notes

## Scope

This service is an operations-assist tool: it prioritizes support tickets for human review. It must not automatically close tickets, alter customer entitlements, or replace escalation policy.

## Data and evaluation

`breach` means the ticket exceeded a documented first-response SLA after a fixed cutoff. Build features only from information available at scoring time; later messages, resolution details, and agent actions are prohibited from the training row. The included synthetic generator exercises the pipeline without customer data.

Threshold selection favors recall while maintaining a validation precision floor. Validate calibration and error rates by priority, channel, and tier before use. Review queue capacity and false-negative cost with support leadership.

## Production controls

Use TLS, workload authentication, request IDs, and access controls. Track schema errors, response time, risk distribution, queue volume, actual breach rate, and feature drift. Version every artifact and only deploy a candidate after a time-based evaluation. The Java caller has finite connection/read timeouts and rejects non-2xx responses; add circuit-breaking and typed JSON parsing for production.
