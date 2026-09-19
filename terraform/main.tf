locals {
  apis = [
    "compute.googleapis.com",
    "storage.googleapis.com",
    "bigquery.googleapis.com",
    "iap.googleapis.com",
    "oslogin.googleapis.com",
  ]
}

resource "google_project_service" "required" {
  for_each = toset(local.apis)

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# --- Identity the VM runs as (attached SA, no downloaded key) ---

resource "google_service_account" "pipeline" {
  account_id   = "settlens-pipeline"
  display_name = "Settlens pipeline (GCE attached SA)"
}

# --- Data lake / warehouse ---

resource "google_storage_bucket" "raw" {
  name                        = "${var.project_id}-settlens-raw"
  location                    = var.storage_location
  uniform_bucket_level_access = true
  force_destroy               = false
}

resource "google_bigquery_dataset" "raw_settlens" {
  dataset_id = var.bq_dataset_id
  location   = var.storage_location
}

# dbt has no generate_schema_name override configured, so every staging/
# intermediate/marts model lands flat in this one dataset (target.schema).
resource "google_bigquery_dataset" "dbt_settlens" {
  dataset_id = var.dbt_dataset_id
  location   = var.storage_location
}

resource "google_storage_bucket_iam_member" "pipeline_bucket_object_admin" {
  bucket = google_storage_bucket.raw.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_bigquery_dataset_iam_member" "pipeline_raw_dataset_editor" {
  dataset_id = google_bigquery_dataset.raw_settlens.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_bigquery_dataset_iam_member" "pipeline_dbt_dataset_editor" {
  dataset_id = google_bigquery_dataset.dbt_settlens.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_project_iam_member" "pipeline_bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.pipeline.email}"
}

# --- Network: no public ports, IAP only ---

resource "google_compute_firewall" "allow_iap_ingress" {
  name    = "allow-iap-ingress"
  network = "default"

  direction     = "INGRESS"
  source_ranges = ["35.235.240.0/20"] # Google's IAP forwarding range
  target_tags   = ["settlens-iap"]

  allow {
    protocol = "tcp"
    ports    = ["22", "8081"]
  }
}

# --- The VM itself ---

resource "google_compute_instance" "airflow_vm" {
  name         = "settlens-airflow-vm"
  machine_type = var.machine_type
  zone         = var.zone
  tags         = ["settlens-iap"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = 30
    }
  }

  network_interface {
    network = "default"
    access_config {} # ephemeral external IP, for outbound internet only (ingress is firewalled to IAP)
  }

  service_account {
    email  = google_service_account.pipeline.email
    scopes = ["cloud-platform"]
  }

  metadata = {
    enable-oslogin = "TRUE"
  }

  depends_on = [google_project_service.required]
}

# --- Team access: IAP tunnel + OS Login for everyone on the project ---

resource "google_project_iam_member" "team_iap_tunnel" {
  for_each = toset(var.team_emails)

  project = var.project_id
  role    = "roles/iap.tunnelResourceAccessor"
  member  = "user:${each.value}"
}

resource "google_project_iam_member" "team_os_login" {
  for_each = toset(var.team_emails)

  project = var.project_id
  role    = "roles/compute.osLogin"
  member  = "user:${each.value}"
}
