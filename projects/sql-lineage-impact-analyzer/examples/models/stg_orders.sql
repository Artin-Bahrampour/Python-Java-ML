WITH normalized AS (
    SELECT
        order_id,
        customer_id,
        CAST(order_timestamp AS TIMESTAMP) AS ordered_at,
        CAST(gross_amount AS DECIMAL(18, 2)) AS gross_amount,
        UPPER(currency_code) AS currency_code
    FROM raw_orders
)
SELECT *
FROM normalized
WHERE gross_amount >= 0
