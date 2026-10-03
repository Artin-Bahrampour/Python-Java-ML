# Settlement Reconciliation Engine

A production-oriented Java 21 service for reconciling internal ledger transactions against an external settlement provider feed.

The system is intentionally framework-light: it uses the Java 21 standard library so the core reconciliation logic remains deterministic, testable, and easy to audit. The architecture separates domain rules from file ingestion, persistence, HTTP delivery, and observability concerns.

## Problem

Financial and payment systems routinely receive settlement files from processors that do not perfectly match the internal ledger. Operations teams need to distinguish:

- exact matches;
- amount or currency mismatches;
- transactions missing from either side;
- duplicate provider records;
- records that cannot be safely matched.

The dangerous failure mode is silently treating an ambiguous record as reconciled. This engine therefore uses explicit match states and conservative reconciliation rules.

## Architecture

```text
                    +-----------------------+
CSV provider -----> |                     | |
CSV ledger -------> |  Reconciliation      | |--> report.csv
                    |  Application         | |--> audit.jsonl
                    +----------+----------+ |
                               |              |
                         domain engine        |
                               |              |
                    +----------v----------+   |
                    | Immutable result    |   |
                    | + metrics + audit   |   |
                    +----------+----------+   |
                               |              |
                     +---------v---------+    |
                     | HTTP operational  |<---+
                     | API /health       |
                     | /metrics         |
                     | /latest         |
                     +-------------------+
```

### Design decisions

1. **Deterministic core** — reconciliation is a pure application operation over typed domain objects.
2. **Conservative matching** — transaction ID is the primary key; amount and currency are validated before an exact match is accepted.
3. **Duplicate detection** — duplicates are surfaced rather than overwritten.
4. **Immutable result model** — reconciliation results are records, making state transitions explicit.
5. **Operational API** — a small HTTP server exposes health, metrics, and the latest report without coupling the domain to HTTP.
6. **Audit trail** — every run writes a JSON Lines audit event containing a run ID, counts, and duration.
7. **No framework dependency in the core** — this keeps startup fast and the domain easy to unit test.

## Requirements

- Java 21+
- Docker (optional)

No Maven/Gradle dependency is required. The project builds with `javac` and runs with the Java standard library.

## Quick start

```bash
./scripts/build.sh
./scripts/test.sh
java -cp build/classes com.artin.reconciliation.Main reconcile \
  --ledger examples/ledger.csv \
  --provider examples/provider.csv \
  --output build/reconciliation-report.csv
```

Expected result: 2 exact matches, 1 amount mismatch, 1 provider-only transaction, and 1 ledger-only transaction.

Start the operational API:

```bash
java -cp build/classes com.artin.reconciliation.Main serve --port 8080
```

Then:

```bash
curl http://localhost:8080/health
curl http://localhost:8080/metrics
curl http://localhost:8080/latest
```

## CLI

### Reconcile

```text
reconcile --ledger <path> --provider <path> --output <path> [--audit <path>]
```

### Serve

```text
serve [--port <1-65535>]
```

The service rejects paths that do not exist, malformed CSV rows, duplicate ledger IDs, invalid monetary values, unsupported currencies, and invalid port values.

## CSV contract

Both input files use:

```csv
transaction_id,amount,currency,settled_at
TX-1001,125.50,NOK,2026-09-29T10:15:00Z
```

`amount` is represented internally as `BigDecimal`; floating-point arithmetic is deliberately avoided for money.

## Reconciliation semantics

| Condition | Result |
|---|---|
| Same ID, amount and currency match | `MATCHED` |
| Same ID, amount differs | `AMOUNT_MISMATCH` |
| Same ID, currency differs | `CURRENCY_MISMATCH` |
| Provider duplicate | `DUPLICATE_PROVIDER` |
| Provider record has no ledger counterpart | `PROVIDER_ONLY` |
| Ledger record has no provider counterpart | `LEDGER_ONLY` |

The report includes the difference amount where applicable.

## Engineering quality

- Java 21 records and sealed domain types where useful
- `BigDecimal` for financial amounts
- deterministic sorting of output
- explicit validation and failure messages
- atomic report replacement using a temporary file + move
- structured JSON logging
- lightweight operational metrics
- bounded HTTP request body handling
- unit tests for matching, duplicates, money handling, CSV parsing, and HTTP behavior
- shell-based build/test scripts with `set -euo pipefail`
- Docker image using a non-root runtime user
- GitHub Actions CI with compilation, tests, and a smoke test

## Threat model notes

This repository does not process real payment credentials or cardholder data. It is a portfolio-grade reconciliation service. For production deployment, transport security, secret management, identity-aware authorization, durable database storage, retention policies, and stronger audit controls would be mandatory.

## Portfolio talking points

This project demonstrates:

- financial-domain modeling;
- deterministic data reconciliation;
- correctness around monetary arithmetic;
- resilient ingestion and validation;
- clean architecture without unnecessary framework complexity;
- operational endpoints and metrics;
- auditability and reproducible outputs;
- automated quality gates and containerization.
