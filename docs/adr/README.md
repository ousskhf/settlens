# Architecture Decision Records

This directory logs significant, hard-to-reverse decisions made on this project: why we chose one approach over another, and what it cost us.

An ADR is a record, not a spec. Once merged, a file is rarely edited. If a decision changes later, write a new ADR that supersedes the old one and update the old one's status, don't rewrite history in place.

## Format

Each ADR follows the standard four-section template (see `0000-template.md`):

- **Status**: Proposed, Accepted, Deprecated, or Superseded by ADR-000N
- **Context**: the problem and constraints that forced a decision
- **Decision**: what we chose, stated plainly
- **Consequences**: what got easier or harder as a result

## When to write one

Write an ADR for: tool/framework choices, naming or schema conventions that are hard to reverse, anything a future contributor will ask "why didn't we just do X" about.

Skip it for reversible, low-stakes changes, a normal PR description is enough for those.

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-single-dbt-project-under-dbt_settlens.md) | Consolidate on a single dbt project: `dbt_settlens` | Accepted |
| [0002](0002-parameterize-gcp-project-via-env-var.md) | Parameterize the BigQuery source project via `GCP_PROJECT_ID` | Accepted |
| [0003](0003-branch-from-latest-main-before-scaffolding.md) | Always branch from latest `main` before scaffolding shared files | Accepted |
| [0004](0004-self-hosted-airflow-via-docker-compose.md) | Orchestrate the batch pipeline with self-hosted Airflow via Docker Compose | Proposed |
