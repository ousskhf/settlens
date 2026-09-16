{{ config(materialized='view') }}


with source as (

    select *
    from {{ source('settlens_raw', 'transactions') }}

),

cleaned as (

    select
        cast(transaction_id as string)
            as transaction_id,
        cast(customer_id as string)
            as customer_id,
        cast(merchant_id as string)
            as merchant_id,
        cast(payment_method_id as string)
            as payment_method_id,
        timestamp_micros(
            div(transaction_created_at, 1000)
        ) as transaction_created_at,
        date(
            timestamp_micros(
                div(transaction_created_at, 1000)
            )
        ) as transaction_date,
        safe_divide(
            cast(amount_minor as numeric),
            100
        ) as amount,
        upper(trim(currency))
            as currency,
        lower(trim(payment_method_type))
            as payment_method_type,
        lower(trim(card_brand))
            as card_brand,
        lower(trim(card_funding))
            as card_funding,
        cast(cardholder_present as bool)
            as cardholder_present,
        lower(trim(authorization_method))
            as authorization_method,
        cast(mcc as string)
            as mcc,
        upper(trim(merchant_country))
            as merchant_country,
        upper(trim(issuer_country))
            as issuer_country,
        cast(is_cross_border as bool)
            as is_cross_border,
        lower(trim(capture_method))
            as capture_method,
        lower(trim(status))
            as status,
        lower(trim(failure_code))
            as failure_code,
        cast(risk_score as float64)
            as risk_score,
        cast(processing_time_ms as int64)
            as processing_time_ms,
        timestamp_micros(
            div(record_created_at, 1000)
        ) as record_created_at,
        timestamp_micros(
            div(record_last_updated, 1000)
        ) as record_last_updated,
        cast(data_version as int64)
            as data_version,
        lower(trim(source_system))
            as source_system

    from source

)

select *
from cleaned


