# Daily Pipeline — How It Works & What To Watch

## The two-stage setup

**Baseline** (`settlens_batch_pipeline`, manual, run once)
Loads the 100K-transaction historical dataset. Covers 2025-09-01 → 2026-08-31.
Uses `WRITE_TRUNCATE` — replaces tables wholesale.

**Daily** (`settlens_daily_pipeline`, `@daily`, `catchup=True`)
Generates + loads one day at a time, starting 2026-09-01. Uses `WRITE_APPEND`.
`catchup=True` is the backfill mechanism — no separate backfill script.

Dimensions (`customers`, `merchants`, `payment_methods`) are **loaded once by
baseline and never regenerated**. Daily only produces `transactions`,
`refunds`, `disputes`, `events`. This guarantees every FK in a daily batch
already exists.

## Things that will bite you

### 1. Two generators share logic by copy, not by import
`generate_daily.py` duplicates the status/risk/failure formulas from the
baseline notebook. **Fix a generator bug in both places or the datasets
silently disagree.** We accepted this to avoid refactoring validated
notebook code under deadline.

### 2. Timestamps are INTEGER, not TIMESTAMP
pandas writes nanosecond precision; BigQuery's parquet loader maps that to
`INTEGER` instead of `TIMESTAMP`. Consequences:
- staging models wrap them: `timestamp_micros(div(col, 1000))`
- `load_daily_bigquery.py` detects the column type and builds its delete
  predicate accordingly

**The real fix** (deferred): add `coerce_timestamps="us",
allow_truncated_timestamps=True` to `to_parquet()` in **both** the notebook
and `generate_daily.py`, then wipe GCS, re-upload, `bq load --replace`, and
strip the `div()` wrapper from staging. ~25 min. Don't do one file without
the other — the schemas must match.

### 3. Volume and merchant concentration differ between baseline and daily
- Baseline: ~274 txns/day, merchants selected uniformly
- Daily: ramps 274 → 7000 over 30 days, merchants Pareto-weighted (a few
  dominate, most are small)

Deliberate, not a bug. Framing: *"early platform history; current data
reflects a maturing marketplace."* Baseline was left alone on purpose.

### 5. dbt tests can fail transiently during backfill
`dbt test` checks the **whole table**, not just the day being loaded. During
a multi-day backfill, run N's tests see days N+1, N+2 not yet loaded. The
failures are real at that instant and resolve once the backfill finishes.

**To fix:** clear the dbt tasks once after backfill completes.
**Open question for the team:** split dbt into its own DAG so ingestion and
data-quality failures are separate signals, and dbt runs once per day rather
than once per backfilled day. Branch ready if we want it.

## Retry safety

`load_daily_bigquery.py` deletes any existing rows for `run_date` before
appending. Re-running the same date is safe — it reloads that day rather
than duplicating it. Look for `Deleted N existing row(s)` in the logs to
confirm the guard fired.

Earlier version swallowed delete errors in a broad `except Exception` and
appended anyway, which produced duplicates. Now only `NotFound` (first-ever
load) is tolerated; everything else fails the task loudly.

## Running it

```bash
# one day, manually
python -m ingestion.generate_daily --run-date 2026-09-01
python -m ingestion.upload_daily   --run-date 2026-09-01
python -m ingestion.load_daily_bigquery --run-date 2026-09-01

# bounded backfill (edit end_date in the DAG, or):
airflow backfill create --dag-id settlens_daily_pipeline \
  --from-date 2026-09-08 --to-date 2026-09-21
```

Don't leave `@daily` running unattended — it needs the VM and scheduler up,
which costs GCP credits for no benefit. Trigger a fresh run right before any
demo so the data is current as of when someone's looking at it.
