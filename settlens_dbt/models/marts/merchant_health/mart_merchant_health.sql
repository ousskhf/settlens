{{
    config(
        materialized='table',
        partition_by={
            "field": "metric_date",
            "data_type": "date",
            "granularity": "day"
        },
        cluster_by=[
            "merchant_id",
            "merchant_tier",
            "risk_category"
        ]
    )
}}

with transactions as (

    select
        transaction_id,
        merchant_id,
        transaction_date as metric_date,
        currency,
        amount,
        status

    from {{ ref('stg_transactions') }}

),

/*
    int_transaction_refunds should be at transaction grain.
    We only need to know whether a transaction has at least one refund.
*/
refunds as (

    select distinct
        transaction_id,
        1 as has_refund

    from {{ ref('int_transaction_refunds') }}

),

/*
    int_transaction_disputes is also transaction-grain.
    Using an intermediate model prevents dispute records from
    multiplying transaction rows in the mart.
*/
disputes as (

    select
        transaction_id,
        has_dispute,
        has_lost_dispute

    from {{ ref('int_transaction_disputes') }}

),

transaction_health as (

    select
        t.transaction_id,
        t.merchant_id,
        t.metric_date,
        t.currency,
        t.amount,
        t.status,

        case
            when t.status = 'succeeded'
            then 1
            else 0
        end as is_successful,

        case
            when t.status = 'requires_payment_method'
            then 1
            else 0
        end as is_failed,

        case
            when t.status in (
                'succeeded',
                'requires_payment_method'
            )
            then 1
            else 0
        end as is_eligible_attempt,

        case
            when t.status = 'canceled'
            then 1
            else 0
        end as is_canceled,

        case
            when t.status = 'requires_action'
            then 1
            else 0
        end as requires_action,

        case
            when t.status = 'processing'
            then 1
            else 0
        end as is_processing,

        coalesce(r.has_refund, 0)
            as has_refund,

        coalesce(d.has_dispute, 0)
            as has_dispute,

        coalesce(d.has_lost_dispute, 0)
            as has_lost_dispute

    from transactions t

    left join refunds r
        using (transaction_id)

    left join disputes d
        using (transaction_id)

),

merchant_daily as (

    select
        metric_date,
        merchant_id,
        currency,

        count(*) as total_transactions,

        sum(is_eligible_attempt)
            as eligible_payment_attempts,

        sum(is_successful)
            as successful_transactions,

        sum(is_failed)
            as failed_transactions,

        sum(is_canceled)
            as canceled_transactions,

        sum(requires_action)
            as requires_action_transactions,

        sum(is_processing)
            as processing_transactions,

        sum(
            case
                when is_eligible_attempt = 1
                then amount
                else 0
            end
        ) as attempted_payment_value,

        sum(
            case
                when is_successful = 1
                then amount
                else 0
            end
        ) as successful_payment_value,

        sum(
            case
                when is_failed = 1
                then amount
                else 0
            end
        ) as failed_payment_value,

        sum(
            case
                when is_successful = 1
                 and has_refund = 1
                then 1
                else 0
            end
        ) as refunded_transactions,

        sum(
            case
                when is_successful = 1
                 and has_dispute = 1
                then 1
                else 0
            end
        ) as disputed_transactions,

        sum(
            case
                when is_successful = 1
                 and has_lost_dispute = 1
                then 1
                else 0
            end
        ) as lost_dispute_transactions

    from transaction_health

    group by
        metric_date,
        merchant_id,
        currency

),

final as (

    select
        md.metric_date,
        md.merchant_id,

        -- Merchant dimensions
        m.merchant_name_token,
        m.mcc,
        m.merchant_category,
        m.merchant_country,
        m.merchant_tier,
        m.risk_category,
        m.settlement_currency,
        m.account_status,
        m.onboarding_date,

        -- Transaction currency is part of the mart grain
        md.currency,

        -- Payment volume
        md.total_transactions,
        md.eligible_payment_attempts,
        md.successful_transactions,
        md.failed_transactions,
        md.canceled_transactions,
        md.requires_action_transactions,
        md.processing_transactions,

        -- Payment value
        md.attempted_payment_value,
        md.successful_payment_value,
        md.failed_payment_value,

        -- Refund / dispute health
        md.refunded_transactions,
        md.disputed_transactions,
        md.lost_dispute_transactions,

        -- Primary merchant health KPIs
        round(
            safe_divide(
                md.successful_transactions,
                md.eligible_payment_attempts
            ) * 100,
            2
        ) as merchant_authorization_rate_pct,

        round(
            safe_divide(
                md.refunded_transactions,
                md.successful_transactions
            ) * 100,
            2
        ) as merchant_refund_rate_pct,

        round(
            safe_divide(
                md.disputed_transactions,
                md.successful_transactions
            ) * 100,
            2
        ) as merchant_dispute_rate_pct,

        round(
            safe_divide(
                md.lost_dispute_transactions,
                md.successful_transactions
            ) * 100,
            2
        ) as merchant_lost_dispute_rate_pct

    from merchant_daily md

    left join {{ ref('stg_merchants') }} m
        using (merchant_id)

)

select *
from final