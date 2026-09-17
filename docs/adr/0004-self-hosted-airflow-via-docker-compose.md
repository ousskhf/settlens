# 0004. Orchestrate the batch pipeline with self-hosted Airflow via Docker Compose

## Status

Proposed, PR [#13](../../pull/13) open since 2026-09-16, implemented on `feat/airflow-batch-pipeline`

## Context

The pipeline (GCS upload → BigQuery raw load → dbt build) was run manually, step by step, on whichever machine happened to have credentials configured. There was no scheduling, no retry behavior, and no single place to see whether a run had actually succeeded end to end. The team sketched the desired DAG shape (`validate_input_files → ingest_raw_to_gcs → load_bigquery_raw → dbt_build_staging → dbt_build_intermediate → dbt_build_marts → pipeline_complete`) in a 2026-09-14 discussion.

Alternatives considered:
- A managed orchestrator (Cloud Composer, MWAA): rejected for now, adds hosting cost and IaC surface the team hasn't set up yet (see Consequences).
- CeleryExecutor with Redis: rejected, the DAG is a single linear pipeline with no need for distributed task queuing.

## Decision

Self-host Airflow 3.3.1 via Docker Compose, using `LocalExecutor` with Postgres only, no Celery or Redis. Pipeline-specific dependencies (`dbt-bigquery`, `google-cloud-*`) install into an isolated `/opt/pysettlens` venv inside the image, kept separate from Airflow's own Python environment to avoid dependency conflicts. `apache-airflow` itself is not a project dependency (not in `pyproject.toml`/poetry), it only lives inside the Docker image. The marts stage selects `path:models/marts` as a single dbt invocation so new marts are picked up automatically without the DAG hard-coding each one.

## Consequences

- Verified end to end via `docker compose exec airflow-scheduler airflow dags test settlens_batch_pipeline <date>`, all 7 tasks succeeded and all 5 marts rebuilt with tests passing (87/87).
- New GCP resources were created directly during testing, outside any IaC: GCS bucket `ousskhf-settlens-raw-2249` and a `storage.objectAdmin` grant on it. These are unmanaged until Terraform is introduced.
- DAG scheduling stays manual-trigger for now; automated scheduling, CI, and a managed-orchestrator migration are explicitly out of scope for this decision and would need their own ADR if pursued.
- Airflow 3.x's split services (`airflow-dag-processor` as a separate mandatory service, `airflow-apiserver` replacing the webserver) and a couple of non-obvious Docker fixes (`ENV HOME=/home/airflow`, self-registering `/etc/passwd` for the compose-assigned UID) are now load-bearing parts of the Dockerfile; anyone upgrading the base image needs to re-verify both.
