with source as (

    select *
    from {{ source('raw', 'disputes') }}

),

renamed as (

    select
        dispute_id,
        transaction_id,

        timestamp_micros(
            div(dispute_created_at, 1000)
        ) as dispute_created_at,

        amount_minor,
        currency,
        dispute_reason,
        dispute_status,

        timestamp_micros(
            div(evidence_due_at, 1000)
        ) as evidence_due_at,

        timestamp_micros(
            div(closed_at, 1000)
        ) as closed_at,

        timestamp_micros(
            div(record_created_at, 1000)
        ) as record_created_at,

        timestamp_micros(
            div(record_last_updated, 1000)
        ) as record_last_updated,

        data_version,
        source_system

    from source

)

select *
from renamed