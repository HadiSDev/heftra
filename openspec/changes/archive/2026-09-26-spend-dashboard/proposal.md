## Why

The dashboard's figures do not measure the same thing, so they cannot be read together: "Net ledger" nets every account (bank, supplier debt, VAT and expense) into a number with no meaning, "Spend by category" adds line amounts as documents print them (often with VAT, so it shows ~DKK 50k against a "ledger" of 10k), and "Transactions" and "Entry types" count postings nobody decides anything from. Nothing on it answers the questions a buyer opens it with: what did we spend this period, is it going up, on what and with whom, and what needs my attention.

## What Changes

- One measure everywhere: **spend** is the net expense the ERP posted, dated by its accounting date, in the company's base currency. It is attributed to categories and suppliers by splitting each voucher's posted spend across its lines' categories by their share of the lines' value (the rule the Spend Lines coverage card already uses), so every figure on the page adds up to every other.
- A **period** control (this month, this quarter, year to date, last 12 months, or custom) with comparison against the preceding period of the same length, and a **company** filter; both live in the URL.
- **Four tiles**: spend in the period with its change and a 12-month sparkline; categorized share of spend; what needs attention (lines to review, documents that failed, invoices whose total disagrees with the ERP), each linking to the filtered Spend Lines; active suppliers with how many are new.
- **Spend over time**: twelve monthly bars stacked by the top categories.
- **Spend by category**: top-level categories with share and change, expandable to the level below.
- **Top suppliers**: spend, share and change, each opening the supplier's page.
- **Insights**: new suppliers, the largest increases, recurring suppliers with their monthly cost, and the largest uncategorized spend.
- **BREAKING** (UI only): the Net ledger, Transactions and Entry types tiles and the line-sum category table are removed from the dashboard. The existing `/reports/*` endpoints stay as they are.
- New read-only endpoints under `/api/v1/reports/`: `spend-overview`, `spend-trend`, `spend-breakdown` and `spend-insights`.
- A charting library (Recharts) is added to the web app for the trend and sparkline.

## Capabilities

### New Capabilities
- `spend-analytics`: the spend measure and its allocation to categories and suppliers, and the tenant-scoped overview, trend, breakdown and insights endpoints built on it.
- `frontend-dashboard`: the dashboard page: period and company controls, tiles, trend chart, category and supplier breakdowns, insights, and their loading, empty and error states.

### Modified Capabilities
- `frontend-auth-dashboard`: the "Dashboard renders live reporting data" requirement changes from stat cards plus one table fed by the ledger reports to the spend dashboard defined in `frontend-dashboard`.
- `web-api-entry-review`: vouchers can be filtered by the state of their document (`document=failed|mismatch`).
- `frontend-erp-entries`: Spend Lines carries that `document` filter in its URL and filter bar.

## Impact

- **web-api**: a `spend_analytics/` package (allocation, periods, and one module per report), a `routers/spend_reports.py`, schemas and tests; the voucher netting moves out of `routers/erp_entries.py` into a shared `vouchers/amounts.py`; a `document` filter on the vouchers queries. No migration.
- **web**: `routes/_authed/index.tsx` rebuilt; `components/dashboard/` replaced by sub-folders for controls, tiles, trend, breakdowns and insights; queries in `lib/api/`; a search-param validator.
- **Dependency**: `recharts` in `apps/web/package.json`, installed by the user (`bun add recharts`).
- **Not in scope**: budgets and targets, forecasting, exports, email digests, and changing the existing `/reports/*` endpoints.
