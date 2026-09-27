## Why

Open CEDA's factors are kg CO₂e per **2023** US dollar. We convert each line's spend to US dollars at the voucher date's rate and multiply by that factor, as if a 2026 dollar bought what a 2023 dollar did. It buys less: US consumer prices rose about 9.7% from the 2023 average to August 2026 (CPI-U 304.7 → 334.1). So every recent estimate is overstated by up to that much, and the overstatement grows each month. The spend-based-emissions proposal left inflation out of scope. Now that the estimate, its calculation and the dashboard are in use, the figures should be in the factor's own dollars.

## What Changes

- A store of **price indices**: monthly values of a named series, starting with US CPI-U (FRED `CPIAUCSL`). A CLI imports it from FRED's public CSV, or from a downloaded file, and can be re-run each month to pick up new values.
- **Deflating spend to the factor set's price year** in the estimate. After conversion to the factor's currency, each line's spend is multiplied by *index for the price year ÷ index for the voucher's month*, and only then by the factor. The price year's index is the average of its twelve months. A month with no published value takes the latest earlier value, which covers the October 2025 gap in CPI and months not yet published. A set whose currency has no index, or whose price year has no values, is estimated unadjusted and says so.
- **The calculation shows the step.** Each line's `emission_calculation` gains the index series, the voucher month's index and the month it came from, the price year's index, and the deflated amount. The line tooltip and the line editor's emissions section show it as a step between the conversion and the factor.
- **The method line says whether figures are adjusted.** It reads, for example, "Spend-based estimate · CEDA 2025 · 2023 USD · adjusted with US CPI". The emissions summary and the dashboard report return which index was used, or none.

## Capabilities

### New Capabilities
- `price-indices`: storing monthly price index series, importing them from FRED or a file, and finding the value for a month and the average for a year.

### Modified Capabilities
- `spend-emissions`: the estimate deflates converted spend to the factor set's price year; the line calculation carries the deflation; the emissions summary and the dashboard report name the index used.
- `frontend-erp-entries`: the line calculation shows the deflation step; the emissions card's method line says whether figures are adjusted.
- `frontend-dashboard`: the emissions section's method line says whether figures are adjusted.

## Impact

- **Order:** `spend-based-emissions` is still an open change. It should be archived first, so this change's deltas modify its synced requirements.
- **web-api**:
  - A new model `PriceIndexValue` and migration `0018_price_indices`.
  - A new `web_api/price_indices/` package: store, lookup and import CLI.
  - Changes to `emissions/estimator.py`, `results.py`, `reads.py` and `vouchers.py`, the calculation and factor-set schemas, and the summary and report builders.
  - The FRED download uses `httpx`, already a dependency. There's no new dependency, and FRED's CSV needs no API key.
- **web**:
  - Types for the new calculation and factor-set fields.
  - `calculationSteps` gains the step.
  - The method line on the emissions card and the dashboard section changes.
- **Data**: the user runs the index import once, then monthly (or when new data is wanted). Until the index is imported, estimates stay unadjusted and the method line says so, so deploying the code changes no figure by surprise.
- **Figures change:** once the index is imported, estimates for 2026 spend fall by about 8–9%, and 2024 spend by about 3%.
- **Out of scope:**
  - Sector-specific deflators, such as BEA's per-industry producer price indices.
  - Deflating in the local currency with its own CPI.
  - Scheduling the monthly index refresh.
