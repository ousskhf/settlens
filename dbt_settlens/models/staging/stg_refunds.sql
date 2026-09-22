with source as (

    select *
    from {{ source('settlens_raw', 'refunds') }}

),

cleaned as (

    select

        cast(refund_id as string)
            as refund_id,

        cast(transaction_id as string)
            as transaction_id,

        currency,

        refund_reason,

        refund_status,

        data_version,
        source_system,
        timestamp_micros(
            div(refund_created_at, 1000)
        ) as refund_created_at,

        date(
            timestamp_micros(
                div(refund_created_at, 1000)
            )
        ) as refund_date,

        safe_divide(
            cast(amount_minor as numeric),
            100
        ) as refund_amount,

        timestamp_micros(
            div(record_created_at, 1000)
        ) as record_created_at,
        timestamp_micros(
            div(record_last_updated, 1000)
        ) as record_last_updated

    from source

)

select *
from cleaned
