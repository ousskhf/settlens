{{ config(materialized='table') }}

with daily as (

    select *
    from {{ ref('int_transactions_customer_daily') }}

),

with_rolling as (

    select

        customer_id,
        transaction_date,

        daily_failure_count as failure_count,
        daily_success_count as successful_payment_count,

        -- RANGE frames with OFFSET PRECEDING require a numeric ORDER BY
        -- key in BigQuery, so we order by day-count-since-epoch rather
        -- than the DATE column directly. "29 preceding" still means a
        -- 30-day inclusive window (today + 29 prior days).
        sum(daily_attempt_count) over (
            partition by customer_id
            order by unix_date(transaction_date)
            range between 29 preceding and current row
        ) as rolling_30d_attempt_count,

        sum(daily_success_count) over (
            partition by customer_id
            order by unix_date(transaction_date)
            range between 29 preceding and current row
        ) as rolling_30d_success_count,

        sum(daily_failure_count) over (
            partition by customer_id
            order by unix_date(transaction_date)
            range between 29 preceding and current row
        ) as rolling_30d_failure_count

    from daily

),

flagged as (

    select

        *,

        -- Threshold for "repeat failure": 2+ failures in the trailing
        -- 30-day window. Not pinned down by the KPI backlog beyond
        -- "start with a simple rolling 30-day threshold" - adjust here
        -- if the team settles on a different N.
        rolling_30d_failure_count >= 2 as is_repeat_failure_customer,

        rolling_30d_attempt_count > 0
            and rolling_30d_success_count = 0
            as no_recent_success_flag

    from with_rolling

)

select *
from flagged
order by transaction_date desc, customer_id
