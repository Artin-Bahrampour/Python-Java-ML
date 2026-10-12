SELECT
    customer_id,
    customer_name,
    country_code,
    updated_at
FROM landing.customers
WHERE customer_id IS NOT NULL
