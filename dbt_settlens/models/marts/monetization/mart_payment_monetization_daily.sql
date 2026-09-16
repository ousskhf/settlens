with transactions as (

    select *
    from {{ ref('stg_transactions') }}

),

refunds as (

    select *
    from {{ ref('int_transaction_refunds') }}

),

enriched_transactions as (

    select
        t.*,

        coalesce(r.refund_count, 0)
            as refund_count,

        coalesce(r.refunded_amount, 0)
            as refunded_amount

    from transactions t

    left join refunds r
        using (transaction_id)

),

daily as (

    select

        transaction_date as metric_date,
        currency,

        count(*) as total_transactions,

        countif(status = 'succeeded')
            as successful_transactions,

        countif(status = 'requires_payment_method')
            as requires_payment_method_transactions,

        countif(status = 'requires_action')
            as requires_action_transactions,

        countif(status = 'canceled')
            as canceled_transactions,

        countif(status = 'processing')
            as processing_transactions,

        safe_divide(
            countif(status = 'succeeded'),
            count(*)
        ) as transaction_success_rate,

        round(sum(amount), 2)
            as transaction_volume,

        round(
            sum(
                case
                    when status = 'succeeded'
                    then amount
                    else 0
                end
            ),
            2
        ) as successful_payment_volume,

        round(
            sum(
                case
                    when status = 'requires_payment_method'
                    then amount
                    else 0
                end
            ),
            2
        ) as requires_payment_method_volume,

        round(
            sum(
                case
                    when status = 'requires_action'
                    then amount
                    else 0
                end
            ),
            2
        ) as requires_action_volume,

        round(
            sum(
                case
                    when status = 'canceled'
                    then amount
                    else 0
                end
            ),
            2
        ) as canceled_payment_volume,

        round(
            sum(
                case
                    when status = 'processing'
                    then amount
                    else 0
                end
            ),
            2
        ) as processing_payment_volume,

        round(
            sum(refunded_amount),
            2
        ) as refund_volume

    from enriched_transactions

    group by
        transaction_date,
        currency

)

select *
from daily
