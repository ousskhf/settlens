{{ config(materialized='table') }}

SELECT
    transaction_date,
    merchant_country,
    payment_method_type,
    card_brand,
    currency,
    count(*) as eligible_transactions,
    SUM(is_successful) as successful_transactions,
    SUM(is_failed) as failed_transactions,
    ROUND(
    100 * SUM(is_successful) / COUNT(*), 2) AS authorization_rate,
    SUM(amount) as total_payment_volume, --need to add exchange rate
    SUM(CASE WHEN is_successful = 1 THEN amount ELSE 0 END)
    AS successful_payment_volume
FROM {{ ref('int_transactions_auth') }}
WHERE payment_method_type = 'card'
GROUP BY
    transaction_date,
    merchant_country,
    payment_method_type,
    card_brand,
    currency
