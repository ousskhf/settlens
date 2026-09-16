{{ config(materialized='table') }}

with failures as (

    select *
    from {{ ref('int_transactions_failure') }}

),

aggregated as (

    select

        transaction_date,
        merchant_country,
        payment_method_type,
        card_brand,
        card_funding,
        currency,
        failure_code,
        failure_category,
        failure_recoverability,

        count(*) as failed_transaction_count,

        round(sum(amount), 2) as failed_payment_value,

        countif(failure_recoverability in ('high', 'medium'))
            as recoverable_transaction_count,

        round(
            sum(
                case
                    when failure_recoverability in ('high', 'medium')
                    then amount
                    else 0
                end
            ),
            2
        ) as recoverable_payment_value

    from failures

    group by
        transaction_date,
        merchant_country,
        payment_method_type,
        card_brand,
        card_funding,
        currency,
        failure_code,
        failure_category,
        failure_recoverability

),

with_ratios as (

    select

        *,

        round(
            safe_divide(recoverable_payment_value, nullif(failed_payment_value, 0)) * 100,
            2
        ) as recoverable_failure_pct,

        round(
            safe_divide(
                failed_payment_value,
                sum(failed_payment_value) over (partition by transaction_date)
            ) * 100,
            2
        ) as failed_value_share_of_day,

        round(
            safe_divide(
                sum(failed_payment_value) over (
                    partition by transaction_date
                    order by failed_payment_value desc
                    rows between unbounded preceding and current row
                ),
                sum(failed_payment_value) over (partition by transaction_date)
            ) * 100,
            2
        ) as cumulative_failed_value_share_of_day

    from aggregated

)

select *
from with_ratios
order by transaction_date desc, failed_payment_value desc
