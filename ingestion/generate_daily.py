"""
Settlens daily synthetic data generator
=======================================

Generates ONE DAY of new payment activity that is consistent with the
baseline dataset produced by the notebook.

Design decisions (the important ones):

1. Customers, merchants and payment methods are NOT regenerated.
   They are loaded from the baseline parquet files, so every
   customer_id / merchant_id / payment_method_id in a daily batch is
   guaranteed to exist in the dimension tables already in BigQuery.

2. The seed varies per day (SEED + days-since-epoch), so each run
   produces different data, but re-running the same date always
   reproduces the identical batch (safe to retry in Airflow).

3. IDs are namespaced by run date, so they can never collide with the
   baseline IDs or with any other day's IDs.

4. The status / risk / failure logic is copied from the baseline
   generator unchanged, so daily KPI ratios (authorisation rate,
   failure mix, cross-border share) match the baseline.

5. Refunds and disputes reference PAST succeeded transactions from the
   baseline, never same-day ones - a refund cannot happen before the
   payment it refunds.

Usage:
    python generate_daily.py --run-date 2026-09-01
    python generate_daily.py                      # defaults to today (UTC)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Config - kept identical to the baseline notebook where it matters
# ---------------------------------------------------------------------------

SEED = 42

BASELINE_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/daily")

# Target steady-state volume once merchant migration matures.
AVG_DAILY_TRANSACTIONS = 1800

# Daily activity starts from the actual historical baseline average
# and progressively increases as merchants migrate more payment volume
# onto Settlens; this keeps dashboard growth visible without a 25x jump.
RAMP_DAYS = 60

# Payments are not flat across the week. Friday/Saturday run hot,
# Sunday runs cold. Monday=0 ... Sunday=6
DOW_MULTIPLIER = {0: 0.95, 1: 1.00, 2: 1.02, 3: 1.06, 4: 1.20, 5: 1.12, 6: 0.80}

REFUND_DAILY_RATE = 0.07      # refunds created today, as a share of daily txn volume
DISPUTE_DAILY_RATE = 0.008    # disputes created today, same basis

COUNTRIES = np.array(["FR", "DE", "GB", "US", "ES", "IT", "NL", "BE", "IN", "JP"])
COUNTRY_WEIGHTS = np.array([0.26, 0.12, 0.11, 0.12, 0.08, 0.08, 0.06, 0.05, 0.07, 0.05])

MCC_MAP = {
    "5411": "grocery",
    "5812": "restaurants",
    "5732": "electronics",
    "4511": "airlines",
    "7011": "hotels",
    "5967": "subscriptions",
    "7995": "gambling",
    "5944": "jewelry",
    "4121": "ride_hailing",
    "4899": "digital_services",
}

CATEGORY_AMOUNT_SCALE = {
    "grocery": 45,
    "restaurants": 55,
    "electronics": 260,
    "airlines": 420,
    "hotels": 310,
    "subscriptions": 25,
    "gambling": 120,
    "jewelry": 480,
    "ride_hailing": 28,
    "digital_services": 42,
}

FAILURE_CODES = np.array([
    "card_declined",
    "insufficient_funds",
    "expired_card",
    "incorrect_cvc",
    "authentication_required",
    "processing_error",
    "do_not_honor",
])
FAILURE_WEIGHTS = np.array([0.34, 0.24, 0.08, 0.07, 0.12, 0.08, 0.07])

# Real payment traffic clusters in waking hours rather than spreading
# evenly across 24h. Index = hour UTC.
HOUR_WEIGHTS = np.array([
    0.010, 0.007, 0.005, 0.004, 0.005, 0.009,   # 00-05
    0.018, 0.032, 0.048, 0.058, 0.062, 0.065,   # 06-11
    0.068, 0.066, 0.062, 0.060, 0.061, 0.066,   # 12-17
    0.072, 0.070, 0.058, 0.044, 0.030, 0.020,   # 18-23
])
HOUR_WEIGHTS = HOUR_WEIGHTS / HOUR_WEIGHTS.sum()

API_VERSION = "synthetic-v1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def daily_id(prefix: str, run_date: str, index: int) -> str:
    """
    Date-namespaced ID. Because the namespace string includes the run
    date and the literal "daily", these can never collide with the
    baseline's stable_id() output or with another day's batch.
    """
    token = uuid.uuid5(
        uuid.NAMESPACE_DNS, f"settlens-daily-{run_date}-{prefix}-{index}"
    ).hex[:24]
    return f"{prefix}_{token}"


def json_dumps(value) -> str:
    return json.dumps(value, separators=(",", ":"), default=str)


def seed_for_date(run_date: pd.Timestamp) -> int:
    """Different every day, identical on a re-run of the same day."""
    days_since_epoch = int(run_date.normalize().value // (24 * 60 * 60 * 10**9))
    return SEED + days_since_epoch


def daily_volume(rng: np.random.Generator, run_date: pd.Timestamp, ramp_start: pd.Timestamp, baseline_daily_avg: float) -> int:
    """
    Day-of-week seasonality, noise, and a ramp-up from the baseline's
    actual average volume to the new steady-state volume over RAMP_DAYS.
    """
    days_in = (run_date.normalize() - ramp_start.normalize()).days
    if days_in < 0:
        days_in = 0
    ramp_progress = min(1.0, days_in / RAMP_DAYS)

    # Use the observed baseline average so the growth curve follows the source data.
    target = baseline_daily_avg + (AVG_DAILY_TRANSACTIONS - baseline_daily_avg) * ramp_progress

    multiplier = DOW_MULTIPLIER[run_date.dayofweek]
    noise = rng.normal(1.0, 0.06)
    return max(1, int(round(target * multiplier * noise)))


def timestamps_within_day(
    rng: np.random.Generator, run_date: pd.Timestamp, n: int
) -> pd.DatetimeIndex:
    """Spread n timestamps across the run date, weighted by hour of day."""
    day_start = run_date.normalize()
    hours = rng.choice(24, size=n, p=HOUR_WEIGHTS)
    minutes = rng.integers(0, 60, size=n)
    seconds = rng.integers(0, 60, size=n)
    micros = rng.integers(0, 1_000_000, size=n)

    offsets = (
        hours.astype("int64") * 3_600_000_000
        + minutes.astype("int64") * 60_000_000
        + seconds.astype("int64") * 1_000_000
        + micros.astype("int64")
    )
    return pd.to_datetime(
        day_start.value + offsets * 1000, utc=True
    ).sort_values()


# ---------------------------------------------------------------------------
# Main generation
# ---------------------------------------------------------------------------

def generate_daily(run_date: str, baseline_dir: Path = BASELINE_DIR) -> dict:
    """
    Generate one day of transactions, refunds, disputes and events.

    Returns a dict of DataFrames keyed by table name.
    """
    run_ts = pd.Timestamp(run_date, tz="UTC")
    run_date_str = run_ts.strftime("%Y-%m-%d")
    rng = np.random.default_rng(seed_for_date(run_ts))

    # --- load existing entities; we never invent new ones ---------------
    customers = pd.read_parquet(baseline_dir / "customers.parquet")
    merchants = pd.read_parquet(baseline_dir / "merchants.parquet")
    payment_methods = pd.read_parquet(baseline_dir / "payment_methods.parquet")
    baseline_txns = pd.read_parquet(baseline_dir / "transactions.parquet")

    # Derive the starting volume from the baseline instead of hard-coding ~274/day.
    baseline_start = baseline_txns["transaction_created_at"].min().normalize()
    baseline_end = baseline_txns["transaction_created_at"].max().normalize()
    baseline_days = (baseline_end - baseline_start).days + 1
    baseline_daily_avg = len(baseline_txns) / baseline_days

    # Start the migration ramp on the first day after the historical baseline ends.
    daily_start = baseline_end + pd.Timedelta(days=1)

    # Only transact with accounts that are actually open.
    active_customers = customers[customers["account_status"] == "active"].reset_index(drop=True)
    active_merchants = merchants[merchants["account_status"] == "active"].reset_index(drop=True)

    # Only payment methods belonging to an active customer are selectable.
    usable_pm = payment_methods[
        payment_methods["customer_id"].isin(set(active_customers["customer_id"]))
    ].reset_index(drop=True)
    pm_indices_by_customer = usable_pm.groupby("customer_id").indices

    # Gradually scale from the historical average as merchants migrate more payment activity.
    n_txn = daily_volume(rng, run_ts, ramp_start=daily_start, baseline_daily_avg=baseline_daily_avg)

    # --- sample the participating entities ------------------------------
    # Customers must have at least one usable payment method.
    eligible_customer_ids = np.array(list(pm_indices_by_customer.keys()))
    txn_customer_ids = rng.choice(eligible_customer_ids, size=n_txn)

    # Merchant selection is deliberately NOT uniform. A fixed (not
    # day-varying) rng seeded from SEED gives every merchant a stable
    # "size" weight from a heavy-tailed distribution - a handful of
    # merchants account for a large share of volume, most see very
    # little, matching how real payment platforms actually look.
    # This is the same rng every call (active_merchants order is stable
    # across days since it's read from the same parquet file), so a
    # given merchant's relative size doesn't fluctuate day to day - only
    # its actual transaction count does, via normal daily sampling.
    structural_rng = np.random.default_rng(SEED)
    raw_weights = structural_rng.pareto(1.6, size=len(active_merchants)) + 1
    merchant_weights = raw_weights / raw_weights.sum()

    merchant_idx = rng.choice(len(active_merchants), size=n_txn, p=merchant_weights)
    txn_merchants = active_merchants.iloc[merchant_idx].reset_index(drop=True)
    txn_merchant_ids = txn_merchants["merchant_id"].to_numpy()

    chosen_pm_row_idx = np.empty(n_txn, dtype=int)
    for i, customer_id in enumerate(txn_customer_ids):
        valid = pm_indices_by_customer[customer_id]
        chosen_pm_row_idx[i] = int(rng.choice(valid))
    txn_pm = usable_pm.iloc[chosen_pm_row_idx].reset_index(drop=True)

    txn_timestamps = timestamps_within_day(rng, run_ts, n_txn)

    # --- amounts (same lognormal-by-category logic as baseline) ---------
    amount_major = np.array([
        max(0.50, min(float(rng.lognormal(np.log(CATEGORY_AMOUNT_SCALE[c]), 0.65)), 5000))
        for c in txn_merchants["merchant_category"]
    ])
    currency = txn_merchants["settlement_currency"].to_numpy()
    amount_minor = np.where(
        currency == "JPY", np.rint(amount_major), np.rint(amount_major * 100)
    ).astype("int64")

    # --- derived transaction attributes ---------------------------------
    pm_type = txn_pm["payment_method_type"].to_numpy()
    issuer_country = txn_pm["issuer_country"].fillna("UNKNOWN").to_numpy()
    merchant_country = txn_merchants["merchant_country"].to_numpy()
    is_cross_border = issuer_country != merchant_country

    cardholder_present = np.zeros(n_txn, dtype=bool)
    authorization_method = np.empty(n_txn, dtype=object)
    for i in range(n_txn):
        if pm_type[i] == "card":
            present = rng.random() < 0.24
            cardholder_present[i] = present
            authorization_method[i] = (
                rng.choice(["chip", "contactless", "swipe"], p=[0.44, 0.49, 0.07])
                if present else "online"
            )
        elif pm_type[i] == "wallet":
            present = rng.random() < 0.18
            cardholder_present[i] = present
            authorization_method[i] = "contactless" if present else "wallet_token"
        else:
            authorization_method[i] = "bank_redirect"

    # --- risk + status: identical formula to baseline -------------------
    base_risk = rng.beta(1.7, 8.5, n_txn)
    merchant_risk_add = txn_merchants["merchant_category"].isin(
        ["gambling", "jewelry"]
    ).to_numpy() * 0.12
    cross_border_add = is_cross_border.astype(float) * 0.08
    prepaid_add = (txn_pm["card_funding"].fillna("") == "prepaid").to_numpy() * 0.07
    risk_score = np.clip(base_risk + merchant_risk_add + cross_border_add + prepaid_add, 0, 1)

    fail_prob = np.clip(0.035 + risk_score * 0.13 + is_cross_border * 0.018, 0.02, 0.28)
    u = rng.random(n_txn)
    status = np.full(n_txn, "succeeded", dtype=object)
    status[u < fail_prob] = "requires_payment_method"

    remaining = u >= fail_prob
    u2 = rng.random(n_txn)
    status[remaining & (u2 < 0.012)] = "canceled"
    status[remaining & (u2 >= 0.012) & (u2 < 0.022)] = "requires_action"
    status[remaining & (u2 >= 0.022) & (u2 < 0.027)] = "processing"

    failure_code = np.full(n_txn, None, dtype=object)
    failed_mask = status == "requires_payment_method"
    if failed_mask.sum() > 0:
        failure_code[failed_mask] = rng.choice(
            FAILURE_CODES, failed_mask.sum(), p=FAILURE_WEIGHTS
        )

    capture_method = rng.choice(
        ["automatic_async", "automatic", "manual"], n_txn, p=[0.68, 0.24, 0.08]
    )
    processing_time_ms = np.clip(
        rng.lognormal(np.log(620), 0.55, size=n_txn)
        + is_cross_border * 160
        + (status != "succeeded") * 120,
        80, 8000,
    ).astype(int)

    transactions = pd.DataFrame({
        "transaction_id": [daily_id("pi", run_date_str, i) for i in range(n_txn)],
        "customer_id": txn_customer_ids,
        "merchant_id": txn_merchant_ids,
        "payment_method_id": txn_pm["payment_method_id"].to_numpy(),
        "transaction_created_at": txn_timestamps,
        "amount_minor": amount_minor,
        "currency": currency,
        "payment_method_type": pm_type,
        "card_brand": txn_pm["card_brand"].to_numpy(),
        "card_funding": txn_pm["card_funding"].to_numpy(),
        "cardholder_present": cardholder_present,
        "authorization_method": authorization_method,
        "mcc": txn_merchants["mcc"].to_numpy(),
        "merchant_country": merchant_country,
        "issuer_country": issuer_country,
        "is_cross_border": is_cross_border,
        "capture_method": capture_method,
        "status": status,
        "failure_code": failure_code,
        "risk_score": np.round(risk_score, 4),
        "processing_time_ms": processing_time_ms,
        "record_created_at": txn_timestamps,
        "record_last_updated": txn_timestamps,
        "data_version": 1,
        "source_system": "synthetic",
    })

    # --- refunds: today's refunds are for PAST payments -----------------
    past_succeeded = baseline_txns[baseline_txns["status"] == "succeeded"]
    n_refunds = int(round(n_txn * REFUND_DAILY_RATE))
    refund_rows = []
    if n_refunds > 0 and len(past_succeeded) > 0:
        picked = past_succeeded.iloc[
            rng.choice(len(past_succeeded), size=n_refunds, replace=False)
        ]
        for i, txn in enumerate(picked.itertuples(index=False)):
            original = int(txn.amount_minor)
            full = rng.random() < 0.38
            amount = original if full else int(max(1, round(original * rng.uniform(0.10, 0.75))))
            created = txn_timestamps[rng.integers(0, n_txn)]
            refund_rows.append({
                "refund_id": daily_id("re", run_date_str, i),
                "transaction_id": txn.transaction_id,
                "refund_created_at": created,
                "amount_minor": amount,
                "currency": txn.currency,
                "refund_reason": rng.choice(
                    ["customer_request", "duplicate", "fraudulent", "product_issue", "service_issue"],
                    p=[0.46, 0.12, 0.08, 0.18, 0.16],
                ),
                "refund_status": rng.choice(["succeeded", "pending", "failed"], p=[0.965, 0.020, 0.015]),
                "initiated_by": rng.choice(["customer", "merchant", "support"], p=[0.42, 0.34, 0.24]),
                "record_created_at": created,
                "record_last_updated": created,
                "data_version": 1,
                "source_system": "synthetic",
            })
    refunds = pd.DataFrame(refund_rows)

    # --- disputes: also against PAST card payments ----------------------
    past_card_succeeded = baseline_txns[
        (baseline_txns["status"] == "succeeded")
        & (baseline_txns["payment_method_type"] == "card")
    ]
    n_disputes = int(round(n_txn * DISPUTE_DAILY_RATE))
    dispute_rows = []
    if n_disputes > 0 and len(past_card_succeeded) > 0:
        picked = past_card_succeeded.iloc[
            rng.choice(len(past_card_succeeded), size=n_disputes, replace=False)
        ]
        for i, txn in enumerate(picked.itertuples(index=False)):
            created = txn_timestamps[rng.integers(0, n_txn)]
            dstatus = rng.choice(
                ["needs_response", "under_review", "won", "lost"], p=[0.27, 0.23, 0.25, 0.25]
            )
            closed = created + pd.Timedelta(days=int(rng.integers(5, 45))) if dstatus in {"won", "lost"} else None
            dispute_rows.append({
                "dispute_id": daily_id("dp", run_date_str, i),
                "transaction_id": txn.transaction_id,
                "dispute_created_at": created,
                "amount_minor": int(txn.amount_minor),
                "currency": txn.currency,
                "dispute_reason": rng.choice(
                    ["fraudulent", "duplicate", "product_not_received",
                     "product_unacceptable", "unrecognized", "credit_not_processed"],
                    p=[0.35, 0.08, 0.18, 0.13, 0.18, 0.08],
                ),
                "dispute_status": dstatus,
                "evidence_due_at": created + pd.Timedelta(days=14),
                "closed_at": closed,
                "record_created_at": created,
                "record_last_updated": closed if closed is not None else created,
                "data_version": 1,
                "source_system": "synthetic",
            })
    disputes = pd.DataFrame(dispute_rows)

    # --- events: lifecycle for today's activity -------------------------
    event_rows = []

    def add_event(event_type, object_type, object_id, created_at,
                  transaction_id=None, customer_id=None, merchant_id=None, payload=None):
        event_rows.append({
            "event_id": daily_id("evt", run_date_str, len(event_rows)),
            "event_type": event_type,
            "object_type": object_type,
            "object_id": object_id,
            "transaction_id": transaction_id,
            "customer_id": customer_id,
            "merchant_id": merchant_id,
            "event_created_at": created_at,
            "api_version": API_VERSION,
            "livemode": False,
            "source_system": "synthetic",
            "payload_json": json_dumps(payload or {}),
            "record_created_at": created_at,
        })

    for txn in transactions.itertuples(index=False):
        base = txn.transaction_created_at
        add_event(
            "payment_intent.created", "payment_intent", txn.transaction_id, base,
            transaction_id=txn.transaction_id, customer_id=txn.customer_id,
            merchant_id=txn.merchant_id,
            payload={"amount_minor": int(txn.amount_minor), "currency": txn.currency,
                     "status": "requires_confirmation"},
        )
        ptime = pd.Timedelta(milliseconds=int(txn.processing_time_ms))
        if txn.status == "succeeded":
            add_event("payment_intent.processing", "payment_intent", txn.transaction_id,
                      base + ptime * 0.55, transaction_id=txn.transaction_id,
                      customer_id=txn.customer_id, merchant_id=txn.merchant_id,
                      payload={"status": "processing"})
            add_event("payment_intent.succeeded", "payment_intent", txn.transaction_id,
                      base + ptime, transaction_id=txn.transaction_id,
                      customer_id=txn.customer_id, merchant_id=txn.merchant_id,
                      payload={"status": "succeeded"})
        elif txn.status == "requires_payment_method":
            add_event("payment_intent.payment_failed", "payment_intent", txn.transaction_id,
                      base + ptime, transaction_id=txn.transaction_id,
                      customer_id=txn.customer_id, merchant_id=txn.merchant_id,
                      payload={"status": txn.status, "failure_code": txn.failure_code})
        elif txn.status == "canceled":
            add_event("payment_intent.canceled", "payment_intent", txn.transaction_id,
                      base + ptime, transaction_id=txn.transaction_id,
                      customer_id=txn.customer_id, merchant_id=txn.merchant_id,
                      payload={"status": "canceled"})
        elif txn.status == "requires_action":
            add_event("payment_intent.requires_action", "payment_intent", txn.transaction_id,
                      base + ptime, transaction_id=txn.transaction_id,
                      customer_id=txn.customer_id, merchant_id=txn.merchant_id,
                      payload={"status": "requires_action"})
        else:
            add_event("payment_intent.processing", "payment_intent", txn.transaction_id,
                      base + ptime, transaction_id=txn.transaction_id,
                      customer_id=txn.customer_id, merchant_id=txn.merchant_id,
                      payload={"status": "processing"})

    txn_lookup = baseline_txns.set_index("transaction_id")[["customer_id", "merchant_id"]]

    for refund in refunds.itertuples(index=False):
        ids = txn_lookup.loc[refund.transaction_id]
        add_event("refund.created", "refund", refund.refund_id, refund.refund_created_at,
                  transaction_id=refund.transaction_id, customer_id=ids["customer_id"],
                  merchant_id=ids["merchant_id"],
                  payload={"amount_minor": int(refund.amount_minor), "currency": refund.currency,
                           "status": refund.refund_status, "reason": refund.refund_reason})

    for dispute in disputes.itertuples(index=False):
        ids = txn_lookup.loc[dispute.transaction_id]
        add_event("charge.dispute.created", "dispute", dispute.dispute_id, dispute.dispute_created_at,
                  transaction_id=dispute.transaction_id, customer_id=ids["customer_id"],
                  merchant_id=ids["merchant_id"],
                  payload={"amount_minor": int(dispute.amount_minor), "currency": dispute.currency,
                           "status": dispute.dispute_status, "reason": dispute.dispute_reason})

    events = pd.DataFrame(event_rows).sort_values(
        ["event_created_at", "event_id"]
    ).reset_index(drop=True)

    return {
        "transactions": transactions,
        "refunds": refunds,
        "disputes": disputes,
        "events": events,
    }


def write_daily(tables: dict, run_date: str, output_dir: Path = OUTPUT_DIR) -> dict:
    """
    Write each table to <output_dir>/<table>/<table>_<run_date>.parquet.

    coerce_timestamps='us' matters: pandas stores datetimes as
    nanoseconds, which BigQuery's parquet loader does not map to
    TIMESTAMP - it lands as INTEGER instead. Microseconds is what
    BigQuery natively supports.
    """
    written = {}
    for name, df in tables.items():
        if df.empty:
            continue
        table_dir = output_dir / name
        table_dir.mkdir(parents=True, exist_ok=True)
        path = table_dir / f"{name}_{run_date}.parquet"
        df.to_parquet(
            path, index=False,
            #Add below if we want to avoid nanosecond issue
            #coerce_timestamps="us", allow_truncated_timestamps=True,
        )
        written[name] = path
    return written


def main():
    parser = argparse.ArgumentParser(description="Generate one day of synthetic payment data")
    parser.add_argument(
        "--run-date",
        default=pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d"),
        help="Date to generate, YYYY-MM-DD (default: today UTC)",
    )
    parser.add_argument("--baseline-dir", default=str(BASELINE_DIR))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    args = parser.parse_args()

    tables = generate_daily(args.run_date, Path(args.baseline_dir))
    written = write_daily(tables, args.run_date, Path(args.output_dir))

    print(f"Run date: {args.run_date}")
    for name, df in tables.items():
        print(f"  {name:<14} {len(df):>7} rows")
    succeeded = (tables["transactions"]["status"] == "succeeded").mean()
    print(f"  authorisation rate: {succeeded:.3f}")
    print()
    for name, path in written.items():
        print(f"  wrote {path}")


if __name__ == "__main__":
    main()