{{ config(materialized='view') }}

with transactions as (

    select *
    from {{ ref('stg_transactions') }}
    where status = 'requires_payment_method'

),

failure_reasons as (

    select *
    from {{ ref('failure_reason_mapping') }}

),

joined as (

    select

        t.transaction_id,
        t.merchant_id,
        t.customer_id,
        t.transaction_date,
        t.transaction_created_at,

        t.amount,
        t.currency,

        t.merchant_country,
        t.issuer_country,
        t.is_cross_border,
        t.payment_method_type,
        t.card_brand,
        t.card_funding,

        t.failure_code,
        fr.failure_category,
        fr.failure_recoverability,
        fr.recovery_action

    from transactions as t
    left join failure_reasons as fr
        on t.failure_code = fr.failure_code

)

select *
from joined
