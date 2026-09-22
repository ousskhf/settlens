{{ config(materialized='table') }}

select
    merchant_id,
    merchant_name_token,

    mcc,
    merchant_category,
    merchant_country,

    merchant_tier,
    risk_category,

    settlement_currency,
    processing_fee_pct,

    account_status,

    onboarding_date,

    coalesce(account_status = 'active', false) as is_active,

    case
        when processing_fee_pct >= 0.03 then 'high'
        when processing_fee_pct >= 0.02 then 'medium'
        else 'low'
    end as processing_fee_band

from {{ ref('stg_merchants') }}
