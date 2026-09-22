with source as (

    select *
    from {{ source('settlens_raw', 'customers') }}

),

cleaned as (

    select

        cast(customer_id as string)
            as customer_id,

        cast(customer_unique_id as string)
            as customer_unique_id,

        cast(data_version as int64)
            as data_version,

        trim(customer_name_token)
            as customer_name_token,

        upper(trim(home_country))
            as home_country,

        upper(trim(preferred_currency))
            as preferred_currency,

        lower(trim(customer_segment))
            as customer_segment,

        lower(trim(customer_value_segment))
            as customer_value_segment,

        lower(trim(risk_level))
            as risk_level,

        lower(trim(account_status))
            as account_status,

        date(
            timestamp_micros(
                div(customer_since_date, 1000)
            )
        ) as customer_since_date,

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
