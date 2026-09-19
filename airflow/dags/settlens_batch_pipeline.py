from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.empty import EmptyOperator

REPO_ROOT = "/opt/repo"
DBT_DIR = f"{REPO_ROOT}/dbt_settlens"
PYSETTLENS_BIN = "/opt/pysettlens/bin"
TASK_ENV = {"PATH": f"{PYSETTLENS_BIN}:/usr/bin:/bin"}

with DAG(
    dag_id="settlens_batch_pipeline",
    description="Ingest raw settlens data into GCS/BigQuery and build the dbt marts",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["settlens"],
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
    },
) as dag:

    validate_input_files = BashOperator(
        task_id="validate_input_files",
        bash_command=f"cd {REPO_ROOT} && make download-data",
    )

    ingest_raw_to_gcs = BashOperator(
        task_id="ingest_raw_to_gcs",
        bash_command=f"cd {REPO_ROOT} && python upload.py",
        env=TASK_ENV,
        append_env=True,
    )

    load_bigquery_raw = BashOperator(
        task_id="load_bigquery_raw",
        bash_command=f"cd {REPO_ROOT} && python -m ingestion.load_bigquery_raw",
        env=TASK_ENV,
        append_env=True,
    )

    dbt_build_staging = BashOperator(
        task_id="dbt_build_staging",
        bash_command=f"cd {DBT_DIR} && dbt seed && dbt build --select path:models/staging --indirect-selection=buildable",
        env=TASK_ENV,
        append_env=True,
    )

    dbt_build_intermediate = BashOperator(
        task_id="dbt_build_intermediate",
        bash_command=f"cd {DBT_DIR} && dbt build --select path:models/intermediate --indirect-selection=buildable",
        env=TASK_ENV,
        append_env=True,
    )

    dbt_build_marts = BashOperator(
        task_id="dbt_build_marts",
        bash_command=f"cd {DBT_DIR} && dbt build --select path:models/marts --indirect-selection=buildable",
        env=TASK_ENV,
        append_env=True,
    )

    pipeline_complete = EmptyOperator(task_id="pipeline_complete")

    (
        validate_input_files
        >> ingest_raw_to_gcs
        >> load_bigquery_raw
        >> dbt_build_staging
        >> dbt_build_intermediate
        >> dbt_build_marts
        >> pipeline_complete
    )
