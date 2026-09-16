from datetime import datetime


def build_blob_path(dataset: str, file_name: str, today: datetime | None = None) -> str:
    """
    Build the GCS blob path for a raw file, shared between the upload
    step and the BigQuery load step so both agree on today's path.
    """
    today = today or datetime.now()
    return f"settlens/raw/{dataset}/{today:%Y}/{today:%m}/{today:%d}/{file_name}"
