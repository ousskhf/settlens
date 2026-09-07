# Settlens

Payment Intelligence Data Platform — Le Wagon data engineering bootcamp final project. Analytics platform only, does not process payments.

## Data

The synthetic MVP dataset (7 tables, Parquet format: customers, merchants, payment_methods, transactions, refunds, disputes, events) is published as a GitHub Release, not committed to git.

```bash
make download-data
```

Downloads and extracts `data-v1` into `data/raw/`. Safe to re-run — skips if the data's already there. Use `make clean-data download-data` to force a fresh download.
