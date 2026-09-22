# 03 — Analytics Marts & Dashboard Design

## 1. Purpose

The mart layer is the consumption layer of Settlens. These models should answer defined business questions without requiring dashboard authors to reconstruct payment logic themselves.

## 2. Mart catalogue

### 2.1 `mart_payment_monetization_daily`

**Grain:** one row per `metric_date` and `currency`.

**Main metrics:**

- total transactions;
- successful transactions;
- transactions requiring a new payment method;
- transactions requiring action;
- cancelled / processing transactions;
- transaction success rate;
- attempted payment volume;
- successful payment volume;
- status-specific payment volume;
- refund volume.

**Business question:** How much payment activity and successful value does the platform process each day?

### 2.2 `mart_card_auth_rates_daily`

**Grain:** one row per date and authorization segment, including geography, method, brand and currency.

**Main metrics:**

- eligible transactions;
- successful transactions;
- failed transactions;
- authorization rate;
- total payment volume;
- successful payment volume.

**Business question:** Where are payment authorizations succeeding or failing?

### 2.3 `mart_payment_failure_opportunity`

**Grain:** one row per date and failure segment.

**Main dimensions:**

- merchant country;
- payment method type;
- card brand;
- card funding;
- currency;
- failure code;
- failure category;
- failure recoverability.

**Main metrics:**

- failed transaction count;
- failed payment value;
- recoverable transaction count;
- recoverable payment value;
- recoverable failure percentage;
- failure-value share of day;
- cumulative failure-value share of day.

**Business question:** Which payment failures represent the largest recoverable opportunity?

### 2.4 `mart_customer_payment_health`

**Grain:** one row per customer per transaction date.

**Main metrics / flags:**

- daily failure count;
- daily successful-payment count;
- rolling 30-day attempt count;
- rolling 30-day success count;
- rolling 30-day failure count;
- repeat-failure flag;
- no-recent-success flag.

**Business question:** Which customers show repeated payment friction or declining payment health?

### 2.5 `mart_merchant_health`

**Grain:** one row per merchant, date and reporting currency.

**Main dimensions:**

- merchant category / MCC;
- country;
- merchant tier;
- risk category;
- settlement currency;
- account status;
- onboarding date.

**Main metrics:**

- transaction counts by status;
- attempted and successful payment value;
- failed payment value;
- refunded transactions;
- disputed transactions;
- lost disputes;
- authorization rate;
- refund rate;
- dispute rate;
- lost-dispute rate.

**Business question:** Which merchants are healthy, deteriorating or operationally risky?

### 2.6 `dim_model` star schema

Unlike the wide, question-specific marts above, `models/marts/dim_model/` publishes a conformed star schema for BI tools that prefer joining dimensions to a fact table:

- `dim_customer` — one row per customer, with segment, risk level and an `is_active` flag.
- `dim_merchant` — one row per merchant, with MCC, tier, risk category and a `processing_fee_band` derived from `processing_fee_pct`.
- `dim_date` — a generated calendar spine (2025-01-01 through 2030-12-31) with year, week, quarter, month and weekday attributes.
- `fact_transactions` — one row per transaction, keyed by `customer_id`, `merchant_id` and `payment_method_id`, sourced from `int_transactions_auth`.

**Business question:** Same underlying data as the marts above, modelled for ad-hoc drill-down and self-service BI rather than a fixed dashboard page.

## 3. Recommended dashboard structure

A single dashboard can be divided into four pages or sections.

### Page 1 — Executive Payment Overview

Primary source: `mart_payment_monetization_daily`

Recommended visuals:

- successful payment volume KPI;
- transaction success rate KPI;
- total payment attempts KPI;
- refund volume KPI;
- daily successful payment volume trend;
- success-rate trend;
- payment-state composition over time;
- currency filter.

### Page 2 — Authorization & Failure Opportunity

Primary sources:

- `mart_card_auth_rates_daily`
- `mart_payment_failure_opportunity`

Recommended visuals:

- authorization rate by country;
- authorization rate by card brand;
- authorization rate by payment method;
- top failure codes by failed value;
- recoverable failed value;
- Pareto chart using cumulative failed-value share;
- recoverability distribution.

This page should help answer: **Where should the team intervene first to recover payment value?**

### Page 3 — Merchant Health

Primary source: `mart_merchant_health`

Recommended visuals:

- merchant authorization-rate distribution;
- merchants with highest failed value;
- refund rate by merchant category;
- dispute rate by merchant tier;
- lost-dispute rate;
- merchant table with conditional formatting and drill-down filters.

### Page 4 — Customer Payment Health

Primary source: `mart_customer_payment_health`

Recommended visuals:

- count of repeat-failure customers;
- count of customers with no recent success;
- rolling failure distribution;
- rolling success trend;
- high-friction customer segments for operational follow-up.

## 4. KPI design rules

Before a metric is displayed, document:

1. **Definition** — the exact formula.
2. **Grain** — what one row represents.
3. **Eligible population** — which transactions enter the denominator.
4. **Time basis** — event date vs ingestion date.
5. **Currency behaviour** — whether values can be summed across currencies.
6. **Null handling** — what a missing rate means.
7. **Source model** — which mart owns the definition.

## 5. Important dashboard cautions

### Do not aggregate money across currencies without conversion

EUR, GBP, USD, INR and JPY values must not be summed into one financial KPI unless an FX conversion layer is introduced.

### Rates need denominator context

A 0% authorization rate on one eligible transaction is very different from 0% on 10,000 transactions. Always expose volume or attempt count alongside rates.

### Null rates can be meaningful

For a merchant/day with no eligible authorization attempts, an authorization rate may correctly be null rather than zero.

### Separate operational and historical dimensions

When using current merchant attributes such as risk category or tier, be explicit about whether the mart represents current-state classification or transaction-time classification.

## 6. Dashboard acceptance checklist

Before the dashboard is considered complete:

- [ ] Every visual uses a documented mart.
- [ ] KPI formulas match dbt definitions.
- [ ] Currency filters or conversion rules are explicit.
- [ ] Date filters use the intended event date.
- [ ] Rates show denominator context.
- [ ] Filters behave consistently across visuals.
- [ ] Dashboard totals reconcile to SQL checks in BigQuery.
- [ ] At least one business action can be taken from each page.

