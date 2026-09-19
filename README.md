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
- `postgres` and the `airflow-*` services have `restart: unless-stopped`, so they come back on their own after a Docker or host restart. `airflow-init` deliberately doesn't (it's a one-shot migration job).

## Deploying to GCP

The same pipeline runs on a GCE VM (`terraform/` provisions the infra, `ansible/` configures and starts it). Everyone with project access (`settlens-lewagon`) can run this - no one owns it exclusively.

**Prerequisites:** `gcloud`, `terraform`, `ansible`, `gh`, and `roles/owner` or `roles/editor` on the GCP project (already granted to the team).

**One-time bootstrap** (skip if someone's already done this):
```bash
gcloud storage buckets create gs://settlens-lewagon-tfstate --project=settlens-lewagon --location=EU --uniform-bucket-level-access
```
Terraform's state lives there so anyone on the team can `plan`/`apply`, not just whoever ran it first.

**Provision/update infra:**
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # defaults are already correct, edit only if needed
terraform init
terraform plan -out=tfplan   # always review before applying
terraform apply tfplan
```

**Deploy/update the app on the VM:**
```bash
cd ansible
cp inventory.ini.example inventory.ini
gcloud compute os-login describe-profile --format='value(posixAccounts[0].username)'   # -> put this in inventory.ini as ansible_user
ansible-playbook playbook.yml
```
First run only: the playbook generates a deploy key and prints it - add it as a **read-only** Deploy Key on the repo's GitHub settings, then rerun the playbook (the `git clone` step fails until the key is added).

**Accessing the deployed instance** (no public ports - everything goes through IAP):
```bash
gcloud compute ssh settlens-airflow-vm --zone=europe-west1-b --tunnel-through-iap
gcloud compute start-iap-tunnel settlens-airflow-vm 8081 --local-host-port=localhost:8081 --zone=europe-west1-b
```
Then browse `http://localhost:8081`. Login is `airflow` / the password in `ansible/.secrets/airflow_admin_password.txt` (generated locally on first deploy, gitignored - ask whoever last ran the playbook if you don't have it).

**Stopping/starting the VM** (to avoid paying for idle compute between demos):
```bash
gcloud compute instances stop settlens-airflow-vm --zone=europe-west1-b
gcloud compute instances start settlens-airflow-vm --zone=europe-west1-b
```
Containers restart automatically once the VM boots - no need to rerun the playbook just for a stop/start.
