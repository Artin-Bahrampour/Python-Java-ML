# Example data models

The SQL files are illustrative transformation models; they are never executed by the analyzer. `landing.orders` and `landing.customers` are intentionally treated as external source tables. All other references between files are inferred from filename stems.

Try changing `raw_orders.sql` and run the impact command to see the transitive effect on `stg_orders` and `mart_daily_revenue`.
