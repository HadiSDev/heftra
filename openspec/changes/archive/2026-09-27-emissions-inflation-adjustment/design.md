## Context

The estimate is in `web_api/emissions/`. `vouchers.estimate_vouchers` loads what a page of vouchers needs, and `Estimator.estimate` works out each line as:

```
kg = share × rate(base → factor currency, voucher date) × factor
```

It returns `LineEmissions`, which `reads._calculation` turns into `EmissionCalculationRead`. The web's `calculationSteps` prints that as three steps. The factor set records its `currency` (USD) and `price_year` (2023), but nothing uses `price_year` today.

**The size of the error.** US CPI-U (FRED `CPIAUCSL`, monthly, seasonally adjusted) averaged 304.703 in 2023 and was 334.131 in August 2026. So August 2026 spend is overstated by 9.7%. FRED's series has no value for October 2025, because the federal shutdown stopped collection that month. Values are published about two weeks after each month ends.

**Constraints:**
- Nothing is stored per voucher; estimates are computed on read.
- The calculation must multiply out to the kg shown.
- The user runs imports and migrations.
- No new dependencies.

## Goals / Non-Goals

**Goals:**
- Express spend in the factor set's price-year dollars before multiplying by the factor.
- Show the deflation as its own step in every line's calculation, naming the index and the months used.
- Keep estimates correct and honest when the index is missing or out of date: unadjusted, and labelled as such.
- Make the index a generic stored series, so a later factor set in another currency or price year needs only a mapping.

**Non-Goals:**
- Sector-specific deflators.
- Local-currency deflation.
- Scheduled refreshes.
- Inflation-adjusting anything other than emissions. Spend figures stay nominal.

## Decisions

### Deflate after converting, with the factor currency's CPI

The calculation becomes:

```
spend × rate(voucher date) = converted (USD, voucher month's prices)
converted × index(price year) ÷ index(voucher month) = deflated (2023 USD)
deflated × factor = kg
```

The factor is per US dollar, so the dollar's own inflation is what separates a 2026 dollar from a 2023 dollar. Converting at the voucher date and then applying US CPI is the standard approach, recommended for spend-based methods including EEIO and CEDA.

*Alternative considered:* deflate in the base currency with that country's CPI (Danish HICP), then convert at a 2023 rate. It is equally defensible, but it needs one index per base currency plus a price-year average FX rate, and it moves the exchange-rate step away from the voucher date that Spend Lines already shows. Rejected for now.

### US CPI-U, not PCE, GDP deflator or sector PPIs

- **CPI-U** (`CPIAUCSL`) is monthly, free, needs no key, and is widely recognised.
- **PCE and the GDP deflator** are close to CPI but quarterly (GDP) or revised more often.
- **BEA's per-industry producer price indices** would fit CEDA's sectors best. But they are annual, lag by more than a year, and need a mapping from all 400 sectors. They are listed as a later refinement.

The series id is stored with each value, so switching indices is a new import plus a one-line mapping.

### Stored monthly values, imported by a CLI

The table is `price_index_values`: `series`, `month` (first day of the month), `value` Numeric(14,4), `source` and `imported_at`, unique on (`series`, `month`). It is a single table with no series table. What the app needs to know about a series lives in code, in `web_api/price_indices/series.py`:

```
INDEX_FOR_CURRENCY = {"USD": PriceSeries(id="CPIAUCSL", label="US CPI")}
```

The CLI is `python -m web_api.price_indices.import_series --series CPIAUCSL [--file <csv>]`. By default it reads `https://fred.stlouisfed.org/graph/fredgraph.csv?id=<series>` with `httpx`. It skips blank or `.` values, then replaces the series' values in one transaction and prints the count and the latest month.

*Alternative considered:* fetch from FRED on read, like FX. Rejected: the values change monthly, a page of vouchers would depend on FRED being up, and estimates must be reproducible from the database.

### The price year's index is its twelve-month average

CEDA's "2023 USD" is an annual price level, so the base is the mean of the price year's twelve monthly values. If any of the twelve is missing, there is no base, and estimates stay unadjusted. A partial average would shift every figure without anyone noticing.

### A missing month takes the latest earlier value

This covers the October 2025 gap and the months not yet published. The calculation always names the month whose value was used (for example, "US CPI Aug 2026"), so a carried-forward value is visible. A voucher dated before the series' first value is left unadjusted. That can't happen with CPI-U, which starts in 1947.

### Where it plugs in

- **`web_api/price_indices/`**:
  - `series.py`: the mapping.
  - `index.py`: `PriceIndex.load(session, series)` holds a series' values in memory. It offers `.average(year)` and `.at(month) -> IndexValue(month, value)`.
  - `import_series.py`: the CLI.
  - `fred.py`: parses the CSV.
- **`web_api/emissions/deflation.py`**: `Deflator(series, base_year, base, index)`, with `.for_date(day) -> Deflation | None`. `Deflation` holds the series label, the month used, its value, the base year and the base value, and applies `× base ÷ value`.
- **`vouchers.estimate_vouchers`**: builds a `Deflator` for the active set's currency and price year when one is available, else `None`. It passes it to `Estimator`, whose `kg` becomes `share × rate × ratio × factor`, rounded only at the end.
- **`LineEmissions`**: gains `deflation: Deflation | None`.
- **`EmissionCalculationRead`**: gains `deflation`, holding `series`, `label`, `month`, `index`, `base_year`, `base_index` and `deflated` (the converted amount × the ratio, to cents). It is null when the estimate is unadjusted.
- **`FactorSetRead`**: gains `price_index`, holding `series`, `label` and `latest_month`, or null. The Spend Lines summary and the dashboard report both use it.
- **Web**:
  - `calculationSteps` inserts "× US CPI 2023 avg 304.70 ÷ Aug 2026 334.13 = US$121.33 in 2023 prices" between the conversion and the factor.
  - The method lines append "adjusted with US CPI", or "not adjusted for inflation" when `price_index` is null.

## Risks / Trade-offs

- **[The index is not re-imported, and carried-forward values go stale]** → The calculation names the month used, and the method line shows the latest month on hover. A later change can schedule the import.
- **[CPI-U is a consumer index; CEDA factors are at purchaser prices for business purchases]** → CPI-U is the common proxy, and the gap to PCE or PPI over three years is about one percentage point. Sector PPIs are recorded as the refinement.
- **[Figures drop by 3–9% on the day the index is imported]** → This is expected. The proposal and the method line explain it, and nothing changes until the user runs the import.
- **[The FRED CSV format changes]** → The parser names the missing header. `--file` accepts a manually downloaded CSV of the same two columns.

## Migration Plan

1. Archive `spend-based-emissions` so its specs are synced.
2. Deploy migration `0018_price_indices`. The user runs it.
3. The user runs `python -m web_api.price_indices.import_series --series CPIAUCSL`.
4. Estimates are adjusted from the next read.

To roll back, delete the series' rows (estimates return to unadjusted) or downgrade the migration.

## Open Questions

- Should a monthly `import_price_index` pipeline run be added now or later? The proposal leaves it out, and the CLI is enough for one company.
