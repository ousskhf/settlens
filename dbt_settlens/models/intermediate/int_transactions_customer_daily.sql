{{ config(materialized='view') }}

with transactions as (

    select *
    from {{ ref('stg_transactions') }}
    where status in ('succeeded', 'requires_payment_method')

),

daily as (

    select

        customer_id,
        transaction_date,

        count(*) as daily_attempt_count,
        countif(status = 'succeeded') as daily_success_count,
        countif(status = 'requires_payment_method') as daily_failure_count

    from transactions

    group by
        customer_id,
        transaction_date

)

select *
from daily
