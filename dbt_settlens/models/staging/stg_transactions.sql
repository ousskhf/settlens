{{ config(materialized='view') }}

SELECT
    transaction_id,
    customer_id,
    merchant_id,
    payment_method_id,
    --cast(transaction_created_at as timestamp) as transaction_created_at,
    timestamp_micros(cast(transaction_created_at / 1000 as int64)) as transaction_created_at,
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
    --cast(record_created_at as timestamp) as record_created_at,
    --cast(record_last_updated as timestamp) as record_last_updated,
    timestamp_micros(cast(record_created_at / 1000 as int64)) as record_created_at,
    timestamp_micros(cast(record_last_updated / 1000 as int64)) as record_last_updated,
    data_version,
    source_system

FROM {{ source('settlens_raw', 'transactions') }}
