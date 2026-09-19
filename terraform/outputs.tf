output "instance_name" {
  value = google_compute_instance.airflow_vm.name
}

output "zone" {
  value = var.zone
}

output "region" {
  value = var.region
}

output "storage_location" {
  value = var.storage_location
}

output "project_id" {
  value = var.project_id
}

output "gcs_bucket_name" {
  value = google_storage_bucket.raw.name
}

output "bq_dataset_id" {
  value = google_bigquery_dataset.raw_settlens.dataset_id
}

output "dbt_dataset_id" {
  value = google_bigquery_dataset.dbt_settlens.dataset_id
}

output "pipeline_service_account_email" {
  value = google_service_account.pipeline.email
}
