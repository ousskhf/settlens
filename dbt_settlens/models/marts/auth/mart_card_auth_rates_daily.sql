{{ config(materialized='table') }}

SELECT
    transaction_date,
    merchant_country,
    payment_method_type,
    card_brand,
    currency,
    count(*) AS eligible_transactions,
    sum(is_successful) AS successful_transactions,
    sum(is_failed) AS failed_transactions,
    round(
        100 * sum(is_successful) / count(*), 2
    ) AS authorization_rate,
    sum(amount) AS total_payment_volume, --need to add exchange rate
    sum(CASE WHEN is_successful = 1 THEN amount_minor ELSE 0 END)
        AS successful_payment_volume
FROM {{ ref('int_transactions_auth') }}
WHERE payment_method_type = 'card'
GROUP BY
    transaction_date,
    merchant_country,
    payment_method_type,
    card_brand,
    currency
