from datetime import datetime
from pathlib import Path
from google.cloud import storage
import os


def upload_to_lake(file_path, dataset, service_account_path=None):
    """
    Upload a local file to the raw zone of a GCS data lake.

    Files are organized using:
        settlens/raw/<dataset>/YYYY/MM/DD/<filename>

    Args:
        file_path (str): Local path to the file.
        dataset (str): Dataset/table name, e.g. "payments".
        service_account_path (str, optional):
            Path to a service account JSON key.
            If None, uses Google Application Default Credentials.

    Returns:
        None
    """

    file_path = Path(file_path)

    # Check that the file exists
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Get current date
    today = datetime.now()

    year = today.strftime("%Y")
    month = today.strftime("%m")
    day = today.strftime("%d")

    # Get only the filename
    file_name = file_path.name

    # Build GCS path
    blob_path = (
        f"settlens/raw/{dataset}/{year}/{month}/{day}/{file_name}"
    )

    print(f"Local file: {file_path}")
    print(f"GCS path: {blob_path}")

    # Create storage client with service account authentication
    if service_account_path:
        # Method 1: Pass service account key file directly to client
        storage_client = storage.Client.from_service_account_json(service_account_path)
    else:
        # Method 2: Use environment variable GOOGLE_APPLICATION_CREDENTIALS
        # or default authentication (if running on GCP)
        storage_client = storage.Client()

    # Get bucket
    bucket_name = os.environ["GCS_BUCKET_NAME"]

    bucket = storage_client.bucket(bucket_name)

    # Upload file
    blob = bucket.blob(blob_path)
    blob.upload_from_filename(str(file_path))

    print("Upload successful!")


if __name__ == "__main__":
    upload_to_lake(
        "data/raw/payments.parquet",
        dataset="payments"
    )
