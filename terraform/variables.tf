variable "project_id" {
  description = "GCP project to deploy into"
  type        = string
  default     = "settlens-lewagon"
}

variable "region" {
  description = "Region for the bucket, dataset, and VM's subnet"
  type        = string
  default     = "europe-west1"
}

variable "zone" {
  description = "Zone for the Compute Engine VM"
  type        = string
  default     = "europe-west1-b"
}

variable "machine_type" {
  description = "Compute Engine machine type for the Airflow/dbt VM"
  type        = string
  default     = "e2-standard-2"
}

variable "bq_dataset_id" {
  description = "BigQuery dataset id for raw data (matches BQ_DATASET in .env)"
  type        = string
  default     = "raw_settlens"
}

variable "dbt_dataset_id" {
  description = "BigQuery dataset id dbt builds staging/intermediate/marts into (matches DBT_DATASET in .env) - single shared dataset, no per-model schema override configured in dbt_project.yml"
  type        = string
  default     = "dbt_settlens"
}

variable "storage_location" {
  description = "Multi-region location for the GCS bucket and BigQuery dataset"
  type        = string
  default     = "EU"
}

variable "team_emails" {
  description = "Google accounts that should get IAP tunnel + OS Login access to the VM"
  type        = list(string)
  default = [
    "ouss.khf@gmail.com",
    "christos.patsalis12@gmail.com",
    "hkrishnan.pro@gmail.com",
  ]
}
