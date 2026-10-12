SELECT
    customer_id,
    customer_name,
    UPPER(country_code) AS country_code,
    updated_at
FROM raw_customers
