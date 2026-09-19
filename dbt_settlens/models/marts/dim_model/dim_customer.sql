{{ config(materialized='table') }}

select
    customer_id,
    customer_unique_id,
    customer_name_token,
    home_country,
    preferred_currency,
    customer_segment,
    customer_value_segment,
    risk_level,
    account_status,
    customer_since_date,
    case
        when account_status = 'active' then true
        else false
    end as is_active

from {{ ref('stg_customers') }}
