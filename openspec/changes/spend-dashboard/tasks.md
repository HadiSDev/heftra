## 1. Shared voucher netting (web-api)

- [x] 1.1 Move `EntryRow` and `InvoiceHeaderState` to `web_api/vouchers/rows.py`, and `_bucket_key`, `_net_spend`, `_voucher_amount`, `_shared`, `_AMOUNT_FIELDS` to `web_api/vouchers/amounts.py` as public functions; the router imports them; existing tests pass unchanged

## 2. Spend allocation and periods (web-api)

- [x] 2.1 Write failing tests for `spend_analytics/periods.py`: comparison period of equal length ending the day before; twelve calendar months ending with a date; `from` after `to` rejected
- [x] 2.2 Implement `periods.py`
- [x] 2.3 Write failing tests for `spend_analytics/allocation.py`: VAT-inclusive lines give the posted net; a split across categories adds up to the posting exactly (remainder to the largest part); uncategorized, failed and missing lines go to "Not categorized"; a posting without an invoice has no supplier; unconverted postings are counted, not summed; only the caller's companies; voucher date is the earliest expense posting's date
- [x] 2.4 Implement `allocation.py` producing `AllocatedSpend` rows for a scope and date window

## 3. Reports (web-api)

- [x] 3.1 Add schemas for the overview, trend, breakdown and insights responses, per base currency
- [x] 3.2 Write failing tests and implement `overview.py`: period and comparison spend, twelve months, categorized spend, active and new suppliers (new by first invoice date to the caller), and attention counts (lines needing review, failed documents, disagreeing totals)
- [x] 3.3 Write failing tests and implement `trend.py`: twelve months with zeros, five top categories named, the rest as "Other", "Not categorized" apart
- [x] 3.4 Write failing tests and implement `breakdown.py`: top-level categories with second-level children and both periods, largest first; top suppliers with both periods, `limit` default 10, max 50, ties by name
- [x] 3.5 Write failing tests and implement `insights.py`: new suppliers, largest increases (rises only), recurring suppliers (spend in at least three of six months, average over active months), largest uncategorized vouchers; each at most five
- [x] 3.6 Add `routers/spend_reports.py` with the four endpoints, `from`/`to`/`company_id` validation (422 for an inverted period, 404 for a foreign company), registered in the app; API tests for scoping and currency separation

## 4. Document filter on vouchers (web-api and web)

- [x] 4.1 Add `document=failed|mismatch` to the vouchers list and summary queries, 422 otherwise, with tests
- [ ] 4.2 Carry `document` in the Spend Lines URL (`validateEntrySearch`) and offer it in the filter bar as "Document failed" and "Total disagrees", with tests

## 5. Dashboard data layer (web)

- [ ] 5.1 Ask the user to install `recharts` (`bun add recharts` in `apps/web`); add `--chart-1`…`--chart-6` and muted chart tokens for light and dark
- [ ] 5.2 Add the response types and `lib/api/spend-reports.ts` query options (keyed by resolved period and company, `keepPreviousData`), with tests of keys and requests
- [ ] 5.3 Add `lib/dashboard-search.ts`: validate `period`, `from`, `to`, `company_id`; resolve presets against today; describe the comparison period for display; with tests

## 6. Dashboard page (web)

- [ ] 6.1 Build `components/dashboard/controls/`: period presets with a custom range, and the company filter
- [ ] 6.2 Build `components/dashboard/tiles/`: Spend (change and sparkline), Categorized, Needs attention (links to the filtered Spend Lines, "All clear"), Suppliers (links to Suppliers); change shown as a percentage, "New", or nothing
- [ ] 6.3 Build `components/dashboard/trend/`: stacked monthly bars per currency with legend, tooltip and a text summary for assistive technology
- [ ] 6.4 Build `components/dashboard/breakdown/`: categories with share bars, change and expandable children; top suppliers opening the supplier page
- [ ] 6.5 Build `components/dashboard/insights/`: the four lists, headings with nothing under them left out, items linking to the supplier or the voucher
- [ ] 6.6 Rebuild `routes/_authed/index.tsx` on the new sections, each with its own placeholder of final size and error state; empty period offers "Last 12 months"; delete the old `stats.tsx`, `category-table.tsx` and `body.tsx`
- [ ] 6.7 Component tests covering each scenario in `frontend-dashboard`, and update the shell test for the dashboard requirement

## 7. Verify

- [ ] 7.1 Run web-api and ai-api pytest, and vitest, tsc, eslint and prettier on the web app, with no regressions
- [ ] 7.2 Check the dashboard in the browser at desktop and phone width against real data: figures agree with Spend Lines' coverage card and the supplier pages, no horizontal scroll, no layout shift on changing the period
