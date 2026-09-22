with disputes as (

    select
        dispute_id,
        transaction_id,
        dispute_created_at,
        dispute_status

    from {{ ref('stg_disputes') }}

),

aggregated as (

    select
        transaction_id,

        1 as has_dispute,

        count(*) as dispute_count,
        min(dispute_created_at) as first_dispute_at,

        max(dispute_created_at) as latest_dispute_at,

        countif(dispute_status = 'lost')
            as lost_dispute_count,

        max(
            case
                when dispute_status = 'lost' then 1
                else 0
            end
        ) as has_lost_dispute

    from disputes

    group by transaction_id

)

select *
from aggregated
