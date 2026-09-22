# Settlens — Looker Studio Dashboard (Sample information)- Later fill this with the common  Project ID info and related data marts

## Architecture

GCS → BigQuery Raw → dbt → BigQuery Marts → Looker Studio

## GCP Project

Set via `GCP_PROJECT_ID` in `.env` (see repo root `README.md`), same as the rest of the pipeline. No hardcoded project.

## BigQuery Dataset

Set via `DBT_DATASET` in `.env`.

## Initial Dashboard Sources

### Merchant Health

`{GCP_PROJECT_ID}.{DBT_DATASET}.mart_merchant_health`

### Payment Monetization

`{GCP_PROJECT_ID}.{DBT_DATASET}.mart_payment_monetization_daily`

### Card Authorization Rates

`{GCP_PROJECT_ID}.{DBT_DATASET}.mart_card_auth_rates_daily`

### Payment Failure Opportunity

`{GCP_PROJECT_ID}.{DBT_DATASET}.mart_payment_failure_opportunity`

### Customer Payment Health

`{GCP_PROJECT_ID}.{DBT_DATASET}.mart_customer_payment_health`

## Dashboard Design

### Page 1 — Merchant Health

- merchant health trend
- merchant performance table
- date filter
- currency filter
- merchant tier / risk category filters where available

### Page 2 — Payment Monetization

- payment volume trend
- transaction trend
- successful transaction trend
- conversion / success metrics where available

## Design Principle

Business logic and KPI definitions remain in dbt.

Looker Studio is used for visualization, filtering and presentation.

## Looker Studio Report

URL: https://datastudio.google.com/u/3/reporting/cdd2be9f-fdca-4a2a-b09f-0eaab150ee4c/page/KxB9F
