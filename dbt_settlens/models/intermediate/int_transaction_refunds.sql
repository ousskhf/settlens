with refunds as (

    select *
    from {{ ref('stg_refunds') }}

),

aggregated as (

    select
        transaction_id,

        count(*) as refund_count,

        round(
            sum(refund_amount),
            2
        ) as refunded_amount

    from refunds

    group by transaction_id

)

select *
from aggregated
