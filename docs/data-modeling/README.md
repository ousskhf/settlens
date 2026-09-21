# Settlens Data Modelling & Analytics Warehouse

This documentation explains how Settlens moves from operational-style synthetic payment data to analytics-ready marts in BigQuery.

The goal is to make the modelling decisions understandable to a new contributor without requiring them to inspect every SQL model first.

## What this documentation covers

1. **Raw source model** — the operational entities, their grain, keys and relationships.
2. **Conceptual and logical model** — why the source schema is normalized and where controlled duplication is intentional.
3. **dbt warehouse layers** — staging, intermediate and mart responsibilities.
4. **Analytics marts** — the business questions each mart answers and the expected grain.
5. **Dashboard design guidance** — which marts should feed which dashboard sections.
6. **Git workflow** — how to add or update documentation safely through feature branches and pull requests.

## Current Settlens modelling flow

```text
Synthetic source generator
        |
        v
CSV / Parquet source files
        |
        v
GCS raw zone
        |
        v
BigQuery raw/external source tables
        |
        v
+-------------------------+
| dbt staging layer       |
| stg_*                   |
| clean + standardize     |
+-------------------------+
        |
        v
+-------------------------+
| dbt intermediate layer  |
| int_*                   |
| reusable business logic |
+-------------------------+
        |
        v
+-------------------------+
| dbt mart layer          |
| mart_*                  |
| analytics-ready tables  |
+-------------------------+
        |
        v
Looker Studio / BI dashboard
```

## Why this is not a pure 3NF warehouse

3NF is useful for understanding source-system modelling and OLTP design because it reduces update anomalies and unnecessary duplication. Settlens uses that thinking to define clear operational entities and keys.

The analytics warehouse is intentionally different. It follows an **ELT / layered analytical modelling pattern**:

- raw source entities preserve operational semantics;
- staging models standardize source fields;
- intermediate models intentionally combine entities and calculate reusable business logic;
- marts intentionally denormalize to make analytical queries simpler and faster.

That separation is important: **normalize for operational integrity; denormalize deliberately for analytics consumption.**

## Documentation files

- [`01_raw_source_model.md`](01_raw_source_model.md) — source entities, conceptual model, logical model and ERD.
- [`02_dbt_warehouse_model.md`](02_dbt_warehouse_model.md) — dbt layers and modelling responsibilities.
- [`03_marts_and_dashboard.md`](03_marts_and_dashboard.md) — mart catalogue, KPI definitions and dashboard ideas.
- [`04_git_workflow.md`](04_git_workflow.md) — branch, commit, push and pull-request workflow.
- [`settlens_source_schema.dbml`](settlens_source_schema.dbml) — DBML source schema used to recreate the ERD.

