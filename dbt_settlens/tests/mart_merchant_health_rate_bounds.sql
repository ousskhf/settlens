select *

from {{ ref('mart_merchant_health') }}

where
       merchant_authorization_rate_pct < 0
    or merchant_authorization_rate_pct > 100

    or merchant_refund_rate_pct < 0
    or merchant_refund_rate_pct > 100

    or merchant_dispute_rate_pct < 0
    or merchant_dispute_rate_pct > 100

    or merchant_lost_dispute_rate_pct < 0
    or merchant_lost_dispute_rate_pct > 100