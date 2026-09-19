# Settlens

Payment Intelligence Data Platform — Le Wagon data engineering bootcamp final project. Analytics platform only, does not process payments.

## Data

The synthetic MVP dataset (7 tables, Parquet format: customers, merchants, payment_methods, transactions, refunds, disputes, events) is published as a GitHub Release, not committed to git.

```bash
make download-data
```

Downloads and extracts `data-v1.1` into `data/raw/`. Safe to re-run — skips if the data's already there. Use `make clean-data download-data` to force a fresh download.

## Running the pipeline with Airflow

The batch pipeline (GCS upload → BigQuery raw load → dbt build) is orchestrated by a self-hosted Airflow instance, run via Docker Compose. It's not tied to this machine: it works the same on any dev machine or server with Docker installed.

**Prerequisites:** Docker and Docker Compose.

**One-time setup:**

1. Copy `.env.example` to `.env` and fill in your own values (`GCP_PROJECT_ID`, `GCS_BUCKET_NAME`, `BQ_DATASET`, `DBT_DATASET`, etc.).
2. Add `AIRFLOW_UID=$(id -u)` to `.env` (run on *this* machine, not copied from elsewhere, so bind-mounted files aren't owned by root).
3. Set up GCP auth: either run `gcloud auth application-default login` (or rely on a GCE VM's attached service account), or drop a service-account key at `./keys/gcp-service-account.json` (gitignored, copy it securely, don't commit it) and set `GOOGLE_APPLICATION_CREDENTIALS` in `.env` to that path.
4. Check port `8081` is free, or change the `airflow-apiserver` port mapping in `docker-compose.yml` if not.

**Start it up:**

```bash
docker compose build
docker compose up airflow-init                 # one-shot: migrates the DB, creates the admin user
docker compose up -d postgres airflow-scheduler airflow-dag-processor airflow-apiserver
```

Open `http://localhost:8081` and log in with `airflow` / `airflow`.

**Notes:**
- New DAGs start **paused** by default. Flip the toggle next to `settlens_batch_pipeline` to activate it.
- The DAG has no schedule (`schedule=None`). It only runs when triggered manually, either the UI's "Trigger DAG" button or `docker compose exec airflow-scheduler airflow dags test settlens_batch_pipeline <date>` from the CLI. It never runs automatically, regardless of whether it's active or paused.
- `docker compose down` stops everything. Add `-v` to also drop the Postgres volume (Airflow's metadata, not your BigQuery data) if you want a clean slate.
