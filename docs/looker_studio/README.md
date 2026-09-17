# Settlens — Looker Studio Dashboard

## Architecture

GCS → BigQuery Raw → dbt → BigQuery Marts → Looker Studio

## GCP Project

`le-wagon-data-2249-2`

## BigQuery Dataset

`settlens_dev`

## Initial Dashboard Sources

### Merchant Health

`le-wagon-data-2249-2.settlens_dev.mart_merchant_health`

### Payment Monetization

`le-wagon-data-2249-2.settlens_dev.mart_payment_monetization_daily`

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
