{{ config(materialized='table') }}

SELECT
    transaction_id,

    -- Foreign keys
    customer_id,
    merchant_id,
    payment_method_id,

    -- Date / time
    transaction_date,
    transaction_created_at,

    -- Transaction measures
    amount_minor,
    currency,

    -- Payment attributes
    payment_method_type,
    card_brand,
    card_funding,
    cardholder_present,
    authorization_method,

    -- Merchant / geography
    mcc,
    merchant_country,
    issuer_country,
    is_cross_border,

    -- Transaction outcome
    capture_method,
    status,
    failure_code,

    -- Risk / processing
    risk_score,
    risk_bucket,
    processing_time_ms,

    -- Analytical flags
    is_successful,
    is_failed

FROM {{ ref('int_transactions_auth') }}
