select *

from {{ ref('mart_merchant_health') }}

where
       eligible_payment_attempts
           != successful_transactions + failed_transactions

    or refunded_transactions > successful_transactions

    or disputed_transactions > successful_transactions

    or lost_dispute_transactions > disputed_transactions

    or failed_payment_value < 0

    or successful_payment_value < 0

    or attempted_payment_value < 0