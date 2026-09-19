# 0002. Parameterize the BigQuery source project via `GCP_PROJECT_ID`

## Status

Accepted, 2026-09-16 (env config groundwork landed earlier in PR #6, 2026-09-10)

## Context

Three of the competing dbt scaffolds (see [0001](0001-single-dbt-project-under-dbt_settlens.md)) each hardcoded a different GCP project ID directly in `sources.yml`'s `database:` field. That meant `main` could only ever build cleanly against whichever single project the last merge happened to hardcode, and every teammate's local BigQuery credentials had to point at that exact project or every mart build failed at the source layer.

PR #6 (`feat: add GCP env config and BigQuery validation`) had already introduced env-driven GCP configuration for the ingestion side. The same pattern needed to extend to dbt's source definitions during the 2026-09-16 consolidation.

## Decision

Replace every hardcoded project ID in `sources.yml` with `env_var('GCP_PROJECT_ID')` (commits `66673da`, `15a367c`, fixed independently on two branches during consolidation). `main` now builds against whatever GCP project the running machine's `.env` sets `GCP_PROJECT_ID` to; `.env.example` documents the variable at the repo root.

## Consequences

- Any teammate, or CI, can run `dbt build` against their own GCP project without editing tracked files, they only need their own `.env`.
- No project ID is committed to the repo, reducing the chance of leaking which GCP project is "real."
- Any new source or seed added to `dbt_settlens/models/staging/sources.yml` must use the same `env_var('GCP_PROJECT_ID')` pattern rather than a literal project ID, or this guarantee silently breaks for that one source.
- This convention was later reused for `BQ_DATASET` in the Airflow orchestration work, see [0004](0004-self-hosted-airflow-via-docker-compose.md), with an added `or 'default'` guard once it turned out `python-dotenv` treats a blank `.env` line as "present but empty," which defeats `env_var()`'s own default.
