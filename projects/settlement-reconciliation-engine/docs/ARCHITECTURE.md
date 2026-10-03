# Architecture Decision Record

## Context

Settlement reconciliation needs correctness and auditability more than framework breadth. The portfolio project should show engineering judgment rather than dependency accumulation.

## Decision

Use Java 21 standard-library components with four boundaries:

- **Domain:** transaction and reconciliation semantics.
- **Application:** orchestration of ingestion, reconciliation, reporting, and audit.
- **Infrastructure:** CSV parsing and atomic filesystem output.
- **API/observability:** HTTP adapter, metrics, and structured logs.

## Why not Spring Boot?

A Spring stack would be reasonable for a larger enterprise service, but this project does not need dependency injection, ORM, or a large HTTP framework to demonstrate the core problem. Avoiding those dependencies keeps the reconciliation engine deterministic and highlights the underlying design. The architecture leaves clear seams for replacing the filesystem adapter with PostgreSQL/object storage and the HTTP adapter with a framework if scale requires it.

## Consistency model

The reconciliation run is batch-oriented. Inputs are immutable for the duration of a run, and the report is written atomically. A failed run therefore does not replace the previous report.

## Scaling path

For larger feeds, the `ReconciliationEngine` can be adapted to stream sorted inputs or use an indexed store. The current implementation intentionally favors readability and bounded in-memory complexity for portfolio-scale datasets.
