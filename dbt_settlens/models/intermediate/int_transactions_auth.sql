{{ config(materialized='view') }}


SELECT
    transaction_id,
    customer_id,
    merchant_id,
    payment_method_id,
    date(transaction_created_at) as transaction_date,
    amount_minor,
    currency,

    payment_method_type,
    card_brand,
    card_funding,
    cardholder_present,
    authorization_method,

    mcc,
    merchant_country,
    issuer_country,
    is_cross_border,

    capture_method,
    status,
    failure_code,
    risk_score,
    processing_time_ms,

    -- Derived fields
    CASE WHEN status = 'succeeded' THEN 1 ELSE 0 END as is_successful,
    CASE WHEN status <> 'succeeded' THEN 1 ELSE 0 END as is_failed,
    CASE
        WHEN risk_score < 0.2 THEN 'low'
        WHEN risk_score < 0.5 THEN 'medium'
        WHEN risk_score < 0.8 THEN 'high'
        else 'very_high'
    END as risk_bucket

FROM {{ ref('stg_transactions') }}
WHERE status <> 'processing'
