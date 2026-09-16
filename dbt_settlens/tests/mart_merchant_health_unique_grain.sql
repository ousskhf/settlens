select
    metric_date,
    merchant_id,
    currency,
    count(*) as row_count

from {{ ref('mart_merchant_health') }}

group by
    metric_date,
    merchant_id,
    currency

having count(*) > 1