import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.empty import EmptyOperator

REPO_ROOT = "/opt/repo"
DBT_DIR = f"{REPO_ROOT}/dbt_settlens"
PYSETTLENS_BIN = "/opt/pysettlens/bin"

# Prepend rather than replace: BashOperator's append_env=True does a dict
# update, so passing PATH here overwrites the container's PATH entirely
# instead of extending it. Reading the real PATH first keeps everything
# the image already provides (e.g. /home/airflow/.local/bin) reachable.
TASK_ENV = {"PATH": f"{PYSETTLENS_BIN}:{os.environ.get('PATH', '/usr/bin:/bin')}"}

with DAG(
    dag_id="settlens_daily_pipeline",
    description="Generate, upload and load ONE DAY of synthetic data, then rebuild the dbt marts",
    # start the day after the baseline dataset ends (baseline covers
    # 2025-09-01 -> 2026-08-31)
    schedule="@daily",
    start_date=datetime(2026, 9, 1),
    # catchup=True backfills every day from start_date up to today, one
    # DAG run per day, each with its own {{ ds }}. This is the backfill
    # mechanism - no separate backfill script needed. Flip to False once
    # the history is filled in if you don't want it running unattended.
    catchup=True,
    # LocalExecutor will happily run several days in parallel during
    # catchup. Each day appends to the same BigQuery tables, so force
    # one at a time to keep the append ordering sane.
    max_active_runs=1,
    tags=["settlens", "daily"],
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
    },
) as dag:

    generate_daily_data = BashOperator(
        task_id="generate_daily_data",
        bash_command=f"cd {REPO_ROOT} && python -m ingestion.generate_daily --run-date {{{{ ds }}}}",
        env=TASK_ENV,
        append_env=True,
    )

    upload_daily_to_gcs = BashOperator(
        task_id="upload_daily_to_gcs",
        bash_command=f"cd {REPO_ROOT} && python -m ingestion.upload_daily --run-date {{{{ ds }}}}",
        env=TASK_ENV,
        append_env=True,
    )

    load_daily_to_bigquery = BashOperator(
        task_id="load_daily_to_bigquery",
        bash_command=f"cd {REPO_ROOT} && python -m ingestion.load_daily_bigquery --run-date {{{{ ds }}}}",
        env=TASK_ENV,
        append_env=True,
    )

    # No `dbt seed` here - seeds are static lookup tables, loaded once by
    # the baseline pipeline. Re-seeding daily would be wasted work.
    dbt_build_staging = BashOperator(
        task_id="dbt_build_staging",
        bash_command=f"cd {DBT_DIR} && dbt build --select path:models/staging --indirect-selection=buildable",
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
        generate_daily_data
        >> upload_daily_to_gcs
        >> load_daily_to_bigquery
        >> dbt_build_staging
        >> dbt_build_intermediate
        >> dbt_build_marts
        >> pipeline_complete
    )
