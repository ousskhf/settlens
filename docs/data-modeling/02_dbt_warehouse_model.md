# 02 — dbt Warehouse Model

## 1. Warehouse objective

The dbt project converts operational-style source data into tested, documented and analytics-ready datasets in BigQuery.

The current BigQuery model contains three logical layers:

```text
RAW / external source
        |
        v
STAGING (`stg_*`)
        |
        v
INTERMEDIATE (`int_*`)
        |
        v
MARTS (`mart_*`)
```

## 2. Staging layer

Current staging models:

- `stg_transactions`
- `stg_customers`
- `stg_merchants`
- `stg_refunds`
- `stg_disputes`

### Responsibility

Staging should remain close to the source while making fields consistent and safe to reuse.

Typical responsibilities include:

- renaming source columns consistently;
- converting transaction amounts from minor units into analytical currency values;
- normalising timestamps into BigQuery `TIMESTAMP` values;
- casting types;
- standardising categorical values;
- exposing source audit fields when required;
- adding lightweight data-quality checks.

### What staging should avoid

- dashboard KPIs;
- broad multi-table aggregation;
- business-specific ranking logic;
- repeated business rules that should be reused by multiple marts.

## 3. Intermediate layer

Current intermediate models visible in BigQuery include:

- `int_transactions_auth`
- `int_transactions_failure`
- `int_transactions_customer_daily`
- `int_transaction_refunds`
- `int_transaction_disputes`

### Responsibility

Intermediate models contain reusable business logic that would otherwise be duplicated across marts.

Examples:

- identifying eligible authorization attempts;
- classifying payment failures;
- calculating customer-day payment behaviour;
- connecting transaction-level refund outcomes;
- connecting dispute outcomes to the originating transaction.

This layer is the correct place for controlled joins and reusable calculations.

## 4. Reference / mapping models

`failure_reason_mapping` is a reference table used to translate processor-style failure codes into analytical classifications such as:

- failure category;
- recoverability;
- prioritisation attributes.

Keeping this mapping separate is preferable to embedding long `CASE WHEN` logic in every downstream mart.

## 5. Mart layer

The mart layer contains business-facing tables designed for direct BI consumption.

Current marts:

- `mart_card_auth_rates_daily`
- `mart_customer_payment_health`
- `mart_merchant_health`
- `mart_payment_failure_opportunity`
- `mart_payment_monetization_daily`

Alongside the wide, question-specific marts above, `models/marts/dim_model/` holds a conformed star schema (`dim_customer`, `dim_merchant`, `dim_date`, `fact_transactions`) for BI tools that prefer joining dimensions to a fact table over querying pre-aggregated marts directly. See [`03_marts_and_dashboard.md`](03_marts_and_dashboard.md) for details.

### Why marts are tables

Marts are read repeatedly by BI tools. Materialising final analytical models as tables avoids recomputing the complete transformation graph every time a dashboard loads and makes BI performance more predictable.

Intermediate and staging logic can remain views where that is appropriate, while high-consumption marts are good candidates for table materialization.

## 6. Modelling principles used

### Principle 1 — define the grain before writing SQL

Every model should have a written grain. Examples:

- one row per transaction;
- one row per customer per day;
- one row per merchant per day and currency;
- one row per failure segment per day.

Most aggregation bugs can be traced back to an unclear grain.

### Principle 2 — preserve a source of truth

Raw source entities should remain replayable. Derived layers can be rebuilt from them.

### Principle 3 — separate cleaning from business logic

Staging standardises. Intermediate models implement reusable business logic. Marts answer business questions.

### Principle 4 — avoid KPI duplication

A KPI definition such as authorization rate or recoverable failure value should be implemented once in a trusted model and reused.

### Principle 5 — use tests as model contracts

Recommended dbt tests include:

- `not_null` on primary identifiers and required date fields;
- `unique` on model grains where uniqueness is expected;
- `relationships` for foreign-key-like warehouse relationships;
- `accepted_values` for controlled statuses/categories;
- custom tests for valid rates, non-negative monetary values and logical status relationships.

### Principle 6 — partition and cluster around access patterns

For large marts, use dates as partition keys when most analysis filters by time. Cluster on common high-cardinality filters such as merchant or customer IDs when it materially improves scan efficiency.

## 7. Recommended repository documentation structure

```text
dbt_settlens/
  models/
    staging/
    intermediate/
    marts/

docs/
  data-modeling/
    README.md
    01_raw_source_model.md
    02_dbt_warehouse_model.md
    03_marts_and_dashboard.md
    settlens_source_schema.dbml
  assets/
    settlens-source-erd.svg
```

## 8. dbt documentation

In addition to Markdown documentation, use dbt's native docs so lineage and column-level descriptions remain close to the SQL models.

Recommended commands:

```bash
dbt build
dbt docs generate
dbt docs serve
```

Before merging a modelling PR, confirm that:

- SQL compiles;
- tests pass;
- model descriptions are present;
- important columns are documented;
- lineage looks correct in dbt docs;
- no unrelated models are included in the PR.

