with source as (

    select *
    from {{ source('settlens_raw', 'merchants') }}

),

cleaned as (

    select

        cast(merchant_id as string)
            as merchant_id,

        cast(mcc as string)
            as mcc,

        cast(processing_fee_pct as numeric)
            as processing_fee_pct,

        cast(data_version as int64)
            as data_version,

        trim(merchant_name_token)
            as merchant_name_token,

        lower(trim(merchant_category))
            as merchant_category,

        upper(trim(merchant_country))
            as merchant_country,

        lower(trim(merchant_tier))
            as merchant_tier,

        lower(trim(risk_category))
            as risk_category,

        upper(trim(settlement_currency))
            as settlement_currency,

        lower(trim(account_status))
            as account_status,

        date(
            timestamp_micros(
                div(onboarding_date, 1000)
            )
        ) as onboarding_date,

        timestamp_micros(
            div(record_created_at, 1000)
        ) as record_created_at,

        timestamp_micros(
            div(record_last_updated, 1000)
        ) as record_last_updated,

        lower(trim(source_system))
            as source_system

    from source

)

select *
from cleaned
