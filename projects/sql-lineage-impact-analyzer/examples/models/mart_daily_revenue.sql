WITH customer_orders AS (
    SELECT
        DATE_TRUNC('day', o.ordered_at) AS order_day,
        c.country_code,
        o.currency_code,
        o.order_id,
        o.gross_amount
    FROM stg_orders AS o
    LEFT JOIN dim_customers AS c
        ON c.customer_id = o.customer_id
)
SELECT
    order_day,
    country_code,
    currency_code,
    COUNT(DISTINCT order_id) AS order_count,
    SUM(gross_amount) AS gross_revenue
FROM customer_orders
GROUP BY order_day, country_code, currency_code
