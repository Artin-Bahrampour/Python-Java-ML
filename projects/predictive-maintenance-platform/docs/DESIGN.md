# Design and operating notes

## Intended use

The API prioritizes candidate inspections for industrial pumps. It is not a machine-control or emergency-shutdown system: an alert must be reviewed by qualified staff alongside operating procedures and direct inspection.

## Data contract and leakage control

The training label is `failure_14d`: an independently verified bearing-related failure in the 14 days after the telemetry cutoff. Every feature must be available at the cutoff time. Maintenance work orders, later technician notes, or post-failure telemetry must never enter the training row.

Required telemetry is a rolling-window summary: operating hours, mean vibration, temperature, pressure, start count, lubricant age, and pump type. The request schema rejects implausible ranges and unknown pump types.

## Model policy

A histogram gradient-boosting classifier handles nonlinear relationships. The model threshold is chosen on a validation set by maximizing recall while meeting a precision floor of 0.35; review the trade-off with reliability engineers before deployment. Persist the artifact's version and metrics with every deployment.

## Operations

* Return HTTP 503 rather than a fabricated risk when no validated artifact exists.
* Monitor input missingness, range violations, latency, API error rate, risk distribution, intervention volume, confirmation rate, and feature drift.
* Retrain only from time-split data and evaluate by asset/site. Compare a candidate to the current model before approval.
* Use TLS, workload authentication, restricted telemetry access, and request logging that excludes raw sensitive operational payloads.

## Java integration

The Java client serializes a telemetry record and calls `POST /v1/risk` with finite connect/read timeouts. In production, parse the response into a typed DTO, add retry/circuit-breaker policy appropriate to the plant network, and route only `schedule_inspection=true` into a human maintenance queue.
