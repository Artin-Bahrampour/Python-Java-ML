# Architecture

## Responsibilities

1. **Safe loader** resolves every input file and verifies that its real path stays under the selected model root. It enforces a 2 MB per-file limit and strict UTF-8 decoding.
2. **SQL parser** delegates dialect-specific parsing to SQLGlot. Exactly one read-only query is accepted per model. CTE aliases are filtered from physical table references.
3. **Dependency resolver** maps the final identifier of each table reference to a model filename, case-insensitively. Unmatched references remain external dependencies.
4. **Graph engine** creates upstream-to-downstream edges, computes a deterministic topological order, detects back-edge cycles, and traverses the reverse graph for impact analysis.
5. **Renderers and CLI** produce stable JSON or readable text. File reports are atomically replaced to avoid partial outputs if the process is interrupted.

## Graph semantics

For `mart_daily_revenue.sql` referencing `stg_orders` and `dim_customers`, the graph contains edges `stg_orders -> mart_daily_revenue` and `dim_customers -> mart_daily_revenue`. An impact query walks outward from changed nodes along downstream edges. The reported distance is the shortest number of edges from any changed model.

## Complexity

Let V be the number of models and E the number of internal dependency edges. Graph construction is O(V + E) aside from sorting; topological ordering and impact traversal are O(V + E). Sorting provides reproducible output at an additional logarithmic factor. SQL parsing cost depends on query size and SQLGlot's dialect parser.

## Deliberate boundaries

- No SQL execution, database connection, credentials, warehouse API, or network calls.
- No automatic rewriting or mutation of model SQL.
- No inference through Jinja/dbt macros or dynamically generated SQL.
- The file stem is the model identity; duplicate stems are rejected rather than guessed.
- Cycles are reported as explicit paths. The topological order only includes nodes that can be safely ordered; if a cycle blocks downstream nodes, those nodes may be absent from the order.
