# Team Workflow

## Task Types

Every task in Notion gets one type, based on [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):

| Type | Use for |
|---|---|
| `feat` | new capability (pipeline stage, dbt model, dashboard view) |
| `fix` | bug fix |
| `refactor` | restructure without behavior change |
| `perf` | performance/optimization |
| `test` | tests, data quality checks (Soda) |
| `docs` | documentation, README, ADRs |
| `build` | build system, IaC, packaging, deps (Terraform/Ansible/Docker/Makefile) |
| `ci` | CI/CD pipeline config (GitHub Actions) |
| `research` | investigation/discovery with no direct commit (KPI definitions, dataset sourcing, architecture exploration) |

Each type has a Notion template with fields tailored to it (context, scope, done-when, etc.) — use it when creating a new task.

## Workflow

```
Notion Task → PR → commit(s)
```

1. **Task** (Notion) — pick a type, fill the template, define "done when."
2. **Branch** — create it off the task type and a short slug:
   ```
   git checkout -b type/short-description
   ```
3. **Commit(s)** — `type: description` convention, same type as the task:
   ```
   git commit -m "type: description"
   ```
4. **PR** — title follows `type: description` (matches the task's type). Body links back to the Notion task URL:
   ```
   gh pr create --title "type: description" --body "Notion: <task URL>"
   ```
   On squash-merge, the PR title becomes the commit message.

`research` tasks stop at step 1 — no branch/PR/commit, since the output is a doc, not code.

## Linking Notion ↔ GitHub

- Notion task: `GitHub PR` URL property — after `gh pr create` returns the PR URL, paste it into this field on the task (manual, no automation).
- PR description: one line — `Notion: <task URL>`

Keep titles clean; linkage lives in structured fields, not text.
