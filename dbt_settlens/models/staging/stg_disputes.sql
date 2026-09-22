with source as (

    select *
    from {{ source('settlens_raw', 'disputes') }}

),

renamed as (

    select
        dispute_id,
        transaction_id,

        amount_minor,

        currency,
        dispute_reason,
        dispute_status,
        data_version,

        source_system,

        timestamp_micros(
            div(dispute_created_at, 1000)
        ) as dispute_created_at,

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
        ) as record_last_updated

    from source

)

select *
from renamed
