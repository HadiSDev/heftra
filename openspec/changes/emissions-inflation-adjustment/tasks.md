## 0. Before starting

- [ ] 0.1 Archive `spend-based-emissions` (with the user's go-ahead) so this change's MODIFIED requirements have synced specs to apply to

## 1. Price indices (web-api)

- [ ] 1.1 Add the `PriceIndexValue` model (`db/models/price_index_value.py`): series, month, value Numeric(14,4), source, imported_at, unique on (series, month). Export it
- [ ] 1.2 Write migration `0018_price_indices`; the downgrade drops the table. Do not run it
- [ ] 1.3 `web_api/price_indices/series.py`: `PriceSeries(id, label)` and `index_for_currency(currency)`, with USD → `CPIAUCSL` "US CPI" (tests)
- [ ] 1.4 `web_api/price_indices/fred.py`: parse a two-column CSV into (month, value) pairs, skipping blank and `.` values, and naming a missing column (tests, including the October 2025 gap)
- [ ] 1.5 `web_api/price_indices/index.py`: `PriceIndex.load(session, series)`, `.average(year)` (none unless all twelve months are present), `.at(day) -> IndexValue(month, value) | None` carrying the latest earlier value forward, and `.latest_month` (tests)
- [ ] 1.6 `web_api/price_indices/import_series.py`: the CLI (`--series`, `--file`). It fetches FRED's CSV with `httpx` when there is no file, replaces the series in one transaction, and prints the count and the latest month (tests with a file and a stubbed fetch; a malformed file changes nothing)
- [ ] 1.7 Make sure company deletion leaves price indices alone (they are global)

## 2. Deflating the estimate (web-api)

- [ ] 2.1 `web_api/emissions/deflation.py`: `Deflation` (label, series, month, index, base_year, base_index, and the ratio) and `Deflator.for_date(day)` (tests)
- [ ] 2.2 `Estimator` takes an optional `Deflator`. kg = share × rate × ratio × factor, rounded once. `LineEmissions` gains `deflation`. Status is unchanged when there's no deflation (tests: adjusted, unadjusted, carried-forward month, mixed across a voucher's date)
- [ ] 2.3 `estimate_vouchers` builds the deflator from the active set's currency and price year, loading the series once per call. None when there is no mapping or no base average
- [ ] 2.4 `EmissionCalculationRead` gains `deflation` (`EmissionDeflationRead`, in its own schema file), and `reads._calculation` fills it with `deflated` rounded to cents (tests: the 65.909 kg scenario multiplies out)
- [ ] 2.5 `FactorSetRead` gains `price_index` (series, label, latest_month), filled by both the vouchers emissions summary and `spend_emissions()` (API tests for adjusted and unadjusted)
- [ ] 2.6 Update the existing emissions tests whose kg change once an index is present. Keep the no-index fixtures, so earlier figures are still checked

## 3. Web

- [ ] 3.1 Types: `EmissionDeflationRead` on the calculation, and `price_index` on `FactorSetRead`
- [ ] 3.2 `calculationSteps`: insert the deflation step when present, e.g. "× US CPI 2023 avg 304.70 ÷ Aug 2026 334.13 = US$121.33 in 2023 dollars" (tests for both shapes)
- [ ] 3.3 The emissions card's and the dashboard section's method lines add "adjusted with US CPI" or "not adjusted for inflation", with the latest month on hover and focus (tests)
- [ ] 3.4 Run vitest, tsc, eslint and prettier on the changed files

## 4. Verification

- [ ] 4.1 Run the web-api suite in full
- [ ] 4.2 With the user's go-ahead: run the migration and import `CPIAUCSL`. Check that a 2026 line's calculation shows the deflation step and multiplies out, and that the dashboard total falls by the expected 8–9% for 2026
- [ ] 4.3 Browser check of the line tooltip, the line editor's calculation, and both method lines
