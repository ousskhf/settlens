terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  backend "gcs" {
    bucket = "settlens-lewagon-tfstate"
    prefix = "settlens"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}
