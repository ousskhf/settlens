import argparse
import os
from datetime import datetime

from google.api_core.exceptions import NotFound
from google.cloud import bigquery

from ingestion.gcs_paths import build_blob_path

DAILY_TABLES = {
    "transactions": "transactions.parquet",
    "refunds": "refunds.parquet",
    "disputes": "disputes.parquet",
    "events": "events.parquet",
}

# Which column identifies "this row belongs to run_date", per table -
# needed for the delete-before-append idempotency guard below.
DAILY_DATE_COLUMNS = {
    "transactions": "transaction_created_at",
    "refunds": "refund_created_at",
    "disputes": "dispute_created_at",
    "events": "event_created_at",
}


def date_predicate(table, date_column):
    """
    Build a SQL expression that reduces date_column to a DATE, handling
    both possible column types.

    pandas writes datetimes as nanosecond ints. Without
    coerce_timestamps='us' on the parquet write, BigQuery's loader maps
    them to INTEGER rather than TIMESTAMP - so the same logical column
    can be either type depending on how the file was produced. Guessing
    wrong here is not a no-op: DATE(INT64) is a hard type error, which
    would make the delete fail and let duplicate rows through.
    """
    field = {f.name: f for f in table.schema}.get(date_column)
    if field is None:
        raise ValueError(
            f"Column {date_column} not found in {table.full_table_id}. "
            f"Available: {[f.name for f in table.schema]}"
        )

    if field.field_type in ("TIMESTAMP", "DATETIME"):
        return f"DATE({date_column})"
    if field.field_type == "DATE":
        return date_column
    if field.field_type in ("INTEGER", "INT64"):
        # nanoseconds since epoch -> DIV (not /) to stay in exact integer
        # arithmetic; float64 cannot represent these magnitudes precisely
        return f"DATE(TIMESTAMP_MICROS(DIV({date_column}, 1000)))"

    raise ValueError(
        f"Cannot build a date predicate for {date_column} "
        f"of type {field.field_type} in {table.full_table_id}"
    )


def delete_existing_day(table, date_column, run_date, bq_client):
    """
    Delete any rows already loaded for run_date before appending fresh
    ones, so re-running the same date does not duplicate rows.

    Any failure here is raised, not swallowed: a silently skipped delete
    followed by an append is exactly how duplicates get in.
    """
    predicate = date_predicate(table, date_column)
    table_ref = table.full_table_id.replace(":", ".")

    query = f"""
        DELETE FROM `{table_ref}`
        WHERE {predicate} = DATE(@run_date)
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("run_date", "DATE", run_date.strftime("%Y-%m-%d")),
        ]
    )
    print(f"  Clearing existing rows for {run_date:%Y-%m-%d} (predicate: {predicate})")
    job = bq_client.query(query, job_config=job_config)
    job.result()
    print(f"  Deleted {job.num_dml_affected_rows} existing row(s)")


def load_daily_table_from_gcs(table_name, file_name, run_date, bucket_name, dataset_id, project_id, bq_client):
    blob_path = build_blob_path(table_name, file_name, today=run_date)
    uri = f"gs://{bucket_name}/{blob_path}"
    table_ref = f"{project_id}.{dataset_id}.{table_name}"

    # Idempotency guard. Only a genuinely missing table is a valid
    # reason to skip the delete (first-ever load) - everything else
    # propagates, because a failed delete plus an append means dupes.
    try:
        table = bq_client.get_table(table_ref)
    except NotFound:
        print(f"  {table_ref} does not exist yet - skipping delete, this is the first load")
    else:
        delete_existing_day(table, DAILY_DATE_COLUMNS[table_name], run_date, bq_client)

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        autodetect=True,
        # APPEND, not TRUNCATE - daily loads add to history. TRUNCATE
        # here would wipe the baseline and every previous day on every run.
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )

    print(f"  Loading {uri} -> {table_ref} (append)")
    load_job = bq_client.load_table_from_uri(uri, table_ref, job_config=job_config)
    load_job.result()

    table = bq_client.get_table(table_ref)
    print(f"  {table_ref} now has {table.num_rows} total rows")


def load_all_daily_tables(run_date, daily_tables=DAILY_TABLES, service_account_path=None):
    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        raise EnvironmentError("GCP_PROJECT_ID is not set. Run: export GCP_PROJECT_ID='<your-project-id>'")

    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        raise EnvironmentError("GCS_BUCKET_NAME is not set. Run: export GCS_BUCKET_NAME='<your-bucket-name>'")

    dataset_id = os.getenv("BQ_DATASET", "raw_settlens")

    if service_account_path:
        bq_client = bigquery.Client.from_service_account_json(service_account_path, project=project_id)
    else:
        bq_client = bigquery.Client(project=project_id)

    for table_name, file_name in daily_tables.items():
        print(f"Loading {table_name} for {run_date:%Y-%m-%d}...")
        load_daily_table_from_gcs(table_name, file_name, run_date, bucket_name, dataset_id, project_id, bq_client)


def main():
    parser = argparse.ArgumentParser(description="Load one day of data from GCS into BigQuery (append, idempotent)")
    parser.add_argument("--run-date", required=True, help="YYYY-MM-DD")
    args = parser.parse_args()

    run_date = datetime.strptime(args.run_date, "%Y-%m-%d")
    load_all_daily_tables(run_date)


if __name__ == "__main__":
    main()
