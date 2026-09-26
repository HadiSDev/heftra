## Context

The dashboard (`routes/_authed/index.tsx`, `components/dashboard/`) renders three stat cards from `GET /reports/entries-summary` (debit less credit over every account, a posting count, an entry-type count) and one table from `GET /reports/spend-by-category` (the sum of categorized lines' `base_amount`, which is VAT-inclusive wherever the document printed its lines so). The two cannot agree.

The rest of the product already has the right measure: the Spend Lines coverage card takes each voucher's net expense posting (`_voucher_amount` in `routers/erp_entries.py`, with `_net_spend` over expense accounts) and splits it by the categorized share of the voucher's lines (`spend_coverage.categorized_share`). The supplier page splits an invoice's net spend across its categories the same way. The ERP's account types were checked against real data and are correct: posted net equals each invoice's net within rounding.

Lines carry their category both as `spend_category_id` and as the path names `level_1`…`level_4`; grouping by the names works across companies on different trees.

Data volumes are small (tens to low thousands of vouchers per organization); reports are read-only and tenant-scoped through `resolve_company_ids`.

## Goals / Non-Goals

**Goals:**
- One spend measure used by every figure on the dashboard, consistent with Spend Lines and the supplier page.
- Period and company controls with a like-for-like comparison.
- Figures that lead somewhere: every count and supplier links to the filtered page that shows it.
- No layout shift, phone width works, loading/empty/error per section.

**Non-Goals:**
- Budgets, targets, forecasting, anomaly detection beyond the listed insights.
- Exports, scheduled digests, saved views.
- Changing or removing the existing `/reports/*` endpoints (other clients may read them).
- Pushing the allocation into SQL; it runs in Python until volumes demand otherwise.

## Decisions

### Allocate once, report many times
A `web_api/spend_analytics/` package holds:
- `allocation.py`: loads the expense postings in scope for a date window, groups them into vouchers, nets them, and splits each voucher across its lines' categories, producing `AllocatedSpend` rows (company, currency, voucher key, invoice id, vendor id, date, `level_1`, `level_2`, categorized flag, amount). Allocated amounts of a voucher are rounded to cents with the remainder given to its largest part, so they add up exactly.
- `periods.py`: `Period(start, end)`, its comparison period (same number of days, ending the day before), and the twelve calendar months ending with a date.
- `overview.py`, `trend.py`, `breakdown.py`, `insights.py`: pure functions over allocated rows plus the few extra facts they need (first invoice date per supplier, attention counts).

Each endpoint loads one window covering everything it needs (for example the comparison period through `to`, or the twelve months ending with `to`) and hands it to its report. Alternative considered: one `GET /reports/dashboard` returning everything. Rejected: a slow insight would hold up the tiles, and each section could not fail or refresh on its own.

### Share the voucher netting with Spend Lines
`_bucket_key`, `_net_spend`, `_voucher_amount`, `_shared` and `_AMOUNT_FIELDS` move from `routers/erp_entries.py` into `web_api/vouchers/amounts.py` (with `EntryRow` and `InvoiceHeaderState` from `routers/entry_rows.py` moving to `web_api/vouchers/rows.py`, so nothing outside the routers imports from them), used by both the router and the allocation, so "a voucher's net spend" has one definition. The router shrinks accordingly; behaviour is unchanged and its tests stay as they are.

### A voucher's date is its expense postings' accounting date
The earliest accounting date among the voucher's expense postings. Invoice dates are not used: some vouchers have no invoice, and the ledger is what the period is about.

### Categories by name, two levels
Grouping uses `level_1` and `level_2` names, "Not categorized" for uncategorized, failed or missing lines and for vouchers without lines. Names not ids, because companies on different trees should add up where the names match, and the dashboard shows names.

### New supplier = first invoice to the caller inside the period
From `min(invoice_date)` over the caller's invoices per vendor, not from the loaded window, so a supplier last used two years ago is not "new".

### Attention counts are current, not per period
Lines needing review, failed documents and disagreeing totals are work to do now, so they are counted over the caller's scope regardless of period, and the links open Spend Lines without a date filter. Disagreeing totals use `reconcile.totals_agree` per invoice.

### A `document` filter on vouchers
`document=failed|mismatch` is added to the vouchers list and summary queries (and to Spend Lines' URL and filter bar), so the attention counts open exactly what they count. `mismatch` is evaluated in Python over the page's candidate invoices using `totals_agree`, as the voucher group already does.

### Recharts for the charts
Stacked monthly bars with tooltips and a legend, and a sparkline, are what Recharts does with little code; hand-built SVG was considered and rejected for the tooltip, axis and resize work it would take. Chart colours come from new `--chart-1`…`--chart-6` tokens (light and dark) so the chart follows the theme; "Other" and "Not categorized" use muted tokens. The user installs it (`bun add recharts`); nothing here runs a package manager.

### Front-end structure
`components/dashboard/` is replaced by `controls/` (period and company), `tiles/` (one file per tile plus the sparkline), `trend/`, `breakdown/` (categories, suppliers) and `insights/`, each with its own loading and error placeholder of its final size. Queries live in `lib/api/spend-reports.ts` with `keepPreviousData`, keyed by the resolved period and company; `lib/dashboard-search.ts` validates the URL and resolves presets to dates against today.

## Risks / Trade-offs

- [Allocation in Python loads every posting in the window] → Windows are at most about two years of one organization's expense postings; if it becomes slow, the allocation can become a SQL query without changing the reports.
- [Lines' `level_*` names drift from the tree when a category is renamed] → Accepted; the stale-category handling on Spend Lines already surfaces them, and re-categorization refreshes them.
- [A voucher with lines of zero total value cannot be split] → Attributed wholly to "Not categorized", so it is visible rather than dropped.
- [Comparing with the months before is not "same period last year"] → Stated in the page ("vs 1 Apr – 30 Jun"); a year-over-year option can follow.
- [New dependency] → Recharts is widely used and tree-shakeable; only the chart components import it.

## Migration Plan

No data migration. Ship the API first (unused until the page switches), then the page. The old dashboard components are deleted in the same change; the old `/reports/*` endpoints stay. Rollback is a revert of the web change.

## Open Questions

- Whether "year to date" should compare with the same span of the previous year. This design compares a period starting on the first of a month with the same days as many calendar months before it (so year to date on 26 September compares with 1 April – 26 December of the year before), for one rule across presets.
