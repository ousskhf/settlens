with source as (

    select *
    from {{ source('raw', 'refunds') }}

),

cleaned as (

    select

        cast(refund_id as string)
            as refund_id,

        cast(transaction_id as string)
            as transaction_id,

        timestamp_micros(
            div(refund_created_at, 1000)
        ) as refund_created_at,

        safe_divide(
            cast(amount_minor as numeric),
            100
        ) as refund_amount

        -- add actual status or metadata fields
        -- only if they exist in the raw schema

    from source

)

select *
from cleaned
