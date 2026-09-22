import os
from google.cloud import bigquery

from ingestion.gcs_paths import build_blob_path

RAW_TABLES = {
    "customers": "customers.parquet",
    "merchants": "merchants.parquet",
    "transactions": "transactions.parquet",
    "payment_methods": "payment_methods.parquet",
    "refunds": "refunds.parquet",
    "disputes": "disputes.parquet",
    "events": "events.parquet",
}


def load_table_from_gcs(
    table_name, file_name, bucket_name, dataset_id, project_id, bq_client
):
    """
    Load a raw table into BigQuery from the GCS object the upload
    step wrote earlier today (same blob path, computed the same way).
    """
    blob_path = build_blob_path(table_name, file_name)
    uri = f"gs://{bucket_name}/{blob_path}"
    table_ref = f"{project_id}.{dataset_id}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    print(f"Loading {uri} -> {table_ref}")
    load_job = bq_client.load_table_from_uri(uri, table_ref, job_config=job_config)
    load_job.result()

    table = bq_client.get_table(table_ref)
    print(f"Loaded {table.num_rows} rows into {table_ref}")


def load_all_raw_tables(raw_tables, service_account_path=None):
    """
    Load multiple raw tables into BigQuery from GCS.

    Args:
        raw_tables (dict):
            Dictionary mapping table names to their GCS file name
            (e.g. "transactions" -> "transactions.parquet").

        service_account_path (str, optional):
            Path to service account JSON key.
    """
    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        raise EnvironmentError(
            "GCP_PROJECT_ID is not set. "
            "Run: export GCP_PROJECT_ID='<your-project-id>'"
        )

    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        raise EnvironmentError(
            "GCS_BUCKET_NAME is not set. "
            "Run: export GCS_BUCKET_NAME='<your-bucket-name>'"
        )

    dataset_id = os.getenv("BQ_DATASET", "raw_settlens")

    if service_account_path:
        bq_client = bigquery.Client.from_service_account_json(
            service_account_path, project=project_id
        )
    else:
        bq_client = bigquery.Client(project=project_id)

    for table_name, file_name in raw_tables.items():
        print(f"Loading {table_name}...")
        load_table_from_gcs(
            table_name, file_name, bucket_name, dataset_id, project_id, bq_client
        )


if __name__ == "__main__":
    load_all_raw_tables(RAW_TABLES)
