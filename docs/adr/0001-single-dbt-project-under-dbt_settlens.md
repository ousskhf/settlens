# 0001. Consolidate on a single dbt project: `dbt_settlens`

## Status

Accepted, 2026-09-16

## Context

Two teammates independently scaffolded separate dbt projects on parallel branches (`feature-dbtmart` and `feature/payment-monetization-daily-mart`, among others): one named `settlens_dbt/`, the other `dbt_settlens/`. Each defined its own source name and schema for the raw layer, and each hardcoded a different GCP project ID in `sources.yml`. By 2026-09-16 this had produced 6 open PRs against `main` (`#6` through `#12`), several of them mart-building branches that only worked against their author's own scaffold.

Merging them as-is would have left `main` with two competing dbt projects, duplicate source definitions, and marts that silently pointed at different warehouses depending on which branch built them.

Alternatives considered:
- Keep both projects and merge them later: rejected, doubles maintenance and every new mart branch would need to pick a side.
- Standardize on `settlens_dbt/`: rejected, only 1 of 4 mart branches used this name.
- Standardize on `dbt_settlens/`: 3 of 4 mart branches already used it.

## Decision

Consolidate on a single project folder and dbt profile name: **`dbt_settlens/`**. Branches scaffolded under `settlens_dbt/` were renamed onto this convention before merging (see `7db09fc`, `b0c78f1`, `d652826`).

Standardize the raw layer on source name `settlens_raw`, schema `raw_settlens`. Adopt one model layering convention across all marts: `models/staging/`, `models/intermediate/`, `models/marts/<domain>/`.

## Consequences

- Any future branch that scaffolds dbt files independently, rather than branching off current `main`, risks recreating this exact duplication. Check that `dbt_settlens/` already exists on `main` before adding new staging or source files.
- Mart branches that predated this consolidation needed a rename pass before merge, which is why several PRs (`#7`, `#10`) show a `refactor: rename settlens_dbt to dbt_settlens for team convention` commit with no functional change.
- New contributors only need to learn one project layout and one source name.

See also [0003](0003-branch-from-latest-main-before-scaffolding.md) for the branching convention adopted to prevent this from recurring.
