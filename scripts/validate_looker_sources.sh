#!/usr/bin/env bash

set -euo pipefail

: "${GCP_PROJECT_ID:?GCP_PROJECT_ID must be set}"
: "${DBT_DATASET:?DBT_DATASET must be set}"

DATASET="${DBT_DATASET}"

TABLES=(
  "mart_card_auth_rates_daily"
  "mart_customer_payment_health"
  "mart_merchant_health"
  "mart_payment_failure_opportunity"
  "mart_payment_monetization_daily"
)

echo "Validating Looker Studio BigQuery sources..."

for TABLE in "${TABLES[@]}"
do
  echo
  echo "Checking ${TABLE}"

  bq query \
    --use_legacy_sql=false \
    --format=pretty \
"
SELECT
    COUNT(*) AS row_count
FROM \`${GCP_PROJECT_ID}.${DATASET}.${TABLE}\`
"
done

echo
echo "All Looker Studio source checks completed."
