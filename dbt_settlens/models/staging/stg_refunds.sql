with source as (

    select *
    from {{ source('settlens_raw', 'refunds') }}

),

renamed as (

    select
        refund_id,
        transaction_id,

        timestamp_micros(
            div(refund_created_at, 1000)
        ) as refund_created_at,

        date(
            timestamp_micros(
                div(refund_created_at, 1000)
            )
        ) as refund_date,

        amount_minor / 100.0 as refund_amount,

        currency,
        refund_reason,
        refund_status,

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