# 0003. Always branch from latest `main` before scaffolding shared files

## Status

Accepted, 2026-09-16

## Context

The 2026-09-16 consolidation (see [0001](0001-single-dbt-project-under-dbt_settlens.md)) had a root cause beyond naming: several mart branches were created before the dbt project even existed on `main`, so each author's branch independently scaffolded `sources.yml`, the dbt profile, and the raw source names, none of them aware another branch was doing the same thing.

A second, separate problem surfaced during the same merge session: a PR opened while stacked on another unmerged branch keeps that branch as its GitHub `baseRefName` even after the base branch merges into `main`. Merging such a PR with `gh pr merge` merges it into the now-stale base branch, not `main`, and the PR still shows `state: MERGED` with nothing to show for it in `git log origin/main`.

## Decision

- Before scaffolding any shared, easy-to-collide file (a new dbt project, `sources.yml`, a shared config), check whether it already exists on current `main`. If it does, branch off it and extend it rather than recreating it.
- Before merging any PR that was opened while another PR was still open, run `gh pr view <n> --json baseRefName` and confirm the base is `main`, not a branch that has since merged. If it's stale, open a fresh PR with the same content targeted at `main` instead of merging the stale one.

## Consequences

- Costs one extra check (`git log main -- <path>` or `gh pr view --json baseRefName`) before scaffolding or merging, cheap compared to a repeat of the 6-PR consolidation.
- Doesn't fully prevent duplicate scaffolding when two branches are cut from `main` at nearly the same moment, that's a coordination problem no branching rule alone solves, but it removes the "I didn't know it already existed" failure mode.
- Reviewers merging a PR should treat "PR shows MERGED but the change isn't on `main`" as a signal to check `baseRefName`, not a sign the merge silently failed.
