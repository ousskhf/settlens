with source as (

    select *
    from {{ source('settlens_raw', 'merchants') }}

),

renamed as (

    select
        merchant_id,
        merchant_name_token,

        mcc,
        merchant_category,
        merchant_country,

        merchant_tier,
        risk_category,

        settlement_currency,
        processing_fee_pct,

        account_status,

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

        data_version,
        source_system

    from source

)

select *
from renamed