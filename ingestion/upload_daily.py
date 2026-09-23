import argparse
import os
from datetime import datetime
from pathlib import Path

from google.cloud import storage

from ingestion.gcs_paths import build_blob_path

# Only these 4 tables change daily. customers/merchants/payment_methods
# stay static (loaded once by the baseline pipeline) - see the "no time
# for SCD2, dims stay static" decision.
DAILY_TABLES = {
    "transactions": "transactions.parquet",
    "refunds": "refunds.parquet",
    "disputes": "disputes.parquet",
    "events": "events.parquet",
}

LOCAL_DAILY_DIR = Path("data/daily")


def upload_daily_file(table_name, gcs_file_name, run_date, storage_client, bucket_name):
    """
    Upload one table's file for one day.

    The local file is named with the date in it (transactions_2026-09-01.parquet)
    to avoid local collisions across days, but is uploaded to GCS as the
    plain table name - the date already lives in the folder path, and
    matching that plain name is what load_daily_bigquery.py expects to
    find via build_blob_path().
    """
    local_path = (
        LOCAL_DAILY_DIR / table_name / f"{table_name}_{run_date:%Y-%m-%d}.parquet"
    )
    if not local_path.is_file():
        raise FileNotFoundError(
            f"Expected daily file not found: {local_path}\n"
            f"Did generate_daily.py run for --run-date {run_date:%Y-%m-%d} first?"
        )

    blob_path = build_blob_path(table_name, gcs_file_name, today=run_date)

    print(f"Local file: {local_path}")
    print(f"GCS path:   gs://{bucket_name}/{blob_path}")

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    blob.upload_from_filename(str(local_path))
    print("Upload successful!")


def upload_all_daily_files(
    run_date, daily_tables=DAILY_TABLES, service_account_path=None
):
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        raise EnvironmentError(
            "GCS_BUCKET_NAME is not set. Run: export GCS_BUCKET_NAME='<your-bucket-name>'"
        )

    if service_account_path:
        storage_client = storage.Client.from_service_account_json(service_account_path)
    else:
        storage_client = storage.Client()

    for table_name, gcs_file_name in daily_tables.items():
        print(f"Uploading {table_name} for {run_date:%Y-%m-%d}...")
        upload_daily_file(
            table_name, gcs_file_name, run_date, storage_client, bucket_name
        )


def main():
    parser = argparse.ArgumentParser(
        description="Upload one day of generated data to GCS"
    )
    parser.add_argument("--run-date", required=True, help="YYYY-MM-DD")
    args = parser.parse_args()

    run_date = datetime.strptime(args.run_date, "%Y-%m-%d")
    upload_all_daily_files(run_date)


if __name__ == "__main__":
    main()
