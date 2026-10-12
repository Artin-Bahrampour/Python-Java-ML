SELECT
    order_id,
    customer_id,
    order_timestamp,
    gross_amount,
    currency_code
FROM landing.orders
WHERE order_id IS NOT NULL
