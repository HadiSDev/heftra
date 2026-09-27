## 1. Data model

- [x] 1.1 Add `EmissionFactorSet`, `EmissionSector`, `EmissionFactor` and `EmissionCountryRegion` models (one file each under `db/models/`) with the uniques and the country-or-region check from the design, and export them
- [x] 1.2 Add `emission_sector_id`, `emission_sector_source` (`EmissionSectorSource` enum: ai, human), `emission_sector_confidence` and `emission_sector_rationale` to `InvoiceLine`
- [x] 1.3 Add `MATCH_EMISSIONS = "match_emissions"` to `PipelineRunKind`
- [x] 1.4 Write migration `0017_emissions` (the tables, the line columns, and the run kind if it is a DB enum); the downgrade drops them. Do not run it
- [x] 1.5 Make company deletion leave factor sets and sectors alone (they are global), and cover it with a test

## 2. Factor sets and import (web-api)

- [x] 2.1 Confirm the Open CEDA workbook's layout from a downloaded copy (done: sheets, 2023 USD, producer price, ISO3, regional averages; recorded in the design)
- [x] 2.2 `web_api/emissions/countries.py`: a static ISO 3166 alpha-3 → alpha-2 table, with tests. Also a local check against the real workbook that every code it holds is known
- [x] 2.3 `web_api/emissions/workbook.py`:
  - [x] 2.3.1 Read the sheets by name and the labels by text
  - [x] 2.3.2 Return the sectors with descriptions, the producer factors per country and region, the purchaser ratios, the country-to-region map, and the set's fields
  - [x] 2.3.3 Name any missing sheet or label
- [x] 2.4 `web_api/emissions/import_factors.py`:
  - [x] 2.4.1 Convert to purchaser prices
  - [x] 2.4.2 Upsert the sectors and replace the version's factors and regions
  - [x] 2.4.3 `--activate` deactivates the rest in one transaction
  - [x] 2.4.4 Print the counts
  - [x] 2.4.5 Tests with a small generated workbook: the happy path, a missing sheet, a purchaser conversion, a re-import
  - [x] 2.4.6 Declare `openpyxl` in web-api's dependencies (the user runs the sync)
- [x] 2.5 `web_api/emissions/factors.py`: `active_factor_set(session)`, plus a `FactorLookup` that loads a set's factors and regions once, then finds a factor for a sector with the four-step fallback and says which area it used (tests)

## 3. Estimate (web-api)

- [x] 3.1 Move `split` out of `spend_analytics/allocation.py` into a shared module both packages import, and keep allocation's behaviour and tests unchanged
- [x] 3.2 `web_api/emissions/estimate.py`:
  - [x] 3.2.1 Split a voucher's net spend across its lines, absorbing discounts
  - [x] 3.2.2 Convert to the set's currency at the voucher date through `FxService`
  - [x] 3.2.3 Multiply by the factor, with the supplier country taken from the vendor, else the printed country, else the company
  - [x] 3.2.4 Return per-line kg, the country used, and the voucher's total and `emissions_status`
- [x] 3.3 Tests on the `Books` builder:
  - [x] 3.3.1 Single line; posted net vs VAT-inclusive lines; discount absorbed
  - [x] 3.3.2 Partial; `no_lines`; `unmatched`; `no_factor`; `unconverted` (stub provider failing); `no_factor_set`
  - [x] 3.3.3 Country fallback
- [x] 3.4 Batch the lookups for a page of vouchers: one query for the lines' sectors and factors, and rates memoized per (currency, date)

## 4. API (web-api)

- [x] 4.1 Add the emissions fields to `VoucherGroupRead` and `InvoiceLineRead`, and fill them in `list_voucher_groups`
- [x] 4.2 `GET /erp-entries/vouchers/emissions`: same filters and scoping as `/summary`, returning the factor set, the total, spend per currency and counts per status (schema in `schemas/erp/`)
- [x] 4.3 `GET /emission-sectors?q=&limit=`: a new router, searching the active classification (limit default 20, max 50)
- [x] 4.4 `PATCH /invoice-lines/{id}` accepts `emission_sector_id`:
  - [x] 4.4.1 A sector sets source `human`; null clears; a sector of another classification gets 422
  - [x] 4.4.2 Audited
  - [x] 4.4.3 Editing item name, description or category clears an `ai` sector
- [x] 4.5 API tests for 4.1–4.4, including tenant scoping and the no-factor-set case
- [x] 4.6 Accept `match_emissions` in `POST /companies/{id}/runs` (test)

## 5. Sector matching (ai-api)

- [x] 5.1 `ai_api/emissions/sector_index.py`: build and query a Qdrant collection per classification from the sector names and descriptions, reusing the `rag/indexer` helpers and an injectable `embed_fn` (tests with a fake embedder)
- [x] 5.2 `ai_api/emissions/line_context.py`: load a line's context for matching: its text, amount, category path, supplier name, country, description and website, and the invoice's other lines. Also its question key (tests)
- [x] 5.3 `ai_api/emissions/agent/`: the four CrewAI tools (search, sector details, supplier profile, other lines), the agent factory (`max_iter=6`), its prompt, and the parsed answer (code or none, plus confidence and rationale). Validate the code against the classification. Test the tools directly, and the answer parsing
- [x] 5.4 `ai_api/emissions/choice/`: the single-shot fallback's numbered prompt and parsed answer, `json_repair` plus pydantic (tests for none, out-of-range and malformed answers)
- [x] 5.5 Sector-match cache, following `persistence/categorization_cache` and keyed by question and classification (tests)
- [x] 5.6 `ai_api/emissions/lines.py` `match_company(session, company_id, *, limit, rematch, run_agent, choose)`:
  - [x] 5.6.1 Select the eligible lines, then use the cache, the agent, or the fallback
  - [x] 5.6.2 Store with source `ai`, never touching `human` lines
  - [x] 5.6.3 Count agent, fallback, unmatched, cached and failed answers
  - [x] 5.6.4 Skip when no set is active
- [x] 5.7 Tests for `match_company` with a stub agent and chooser:
  - [x] 5.7.1 Human lines untouched; re-match on a new classification
  - [x] 5.7.2 Cache hits counted; `--rematch` clears only `ai`
  - [x] 5.7.3 Agent failure falls back; both failing counts as failed
- [x] 5.8 `ai_api/emissions/runner.py` CLI (`--company-id`, `--limit`, `--rematch`), and a `match_emissions` executor in `worker/executors.py` (tests)

## 6. Frontend

- [x] 6.1 Types and queries:
  - [x] 6.1.1 Emissions fields on vouchers and lines
  - [x] 6.1.2 `voucherEmissionsQueryOptions` (keyed on the filters, `keepPreviousData`) and `emissionSectorsQueryOptions`
  - [x] 6.1.3 `emission_sector_id` on the line update
  - [x] 6.1.4 `match_emissions` in the run kinds and labels
- [x] 6.2 `formatEmissions(kg)`: kg below 1,000, t with one decimal above, at most 3 significant figures (tests)
- [x] 6.3 `components/entries/summary/emissions-card.tsx`:
  - [x] 6.3.1 Total, share estimated per currency, method line and attribution
  - [x] 6.3.2 Not-estimated counts with reasons
  - [x] 6.3.3 Its own loading, error and retry states, fixed height, and the no-factor-set state
  - [x] 6.3.4 Placed beside the coverage card in `entries-panel.tsx`
- [x] 6.4 A CO₂e column in the voucher table (partial mark, "—" with reason). Each expanded line shows its sector with an AI/human mark, a needs-review mark below the threshold, its CO₂e, and the rationale and factor area on hover and focus
- [x] 6.5 An emission sector picker in the line editor: a debounced server search, name and code shown, clearable, disabled with an explanation when no set is active; saving invalidates the voucher list and the emissions summary
- [x] 6.6 Component tests for the card, the column and line display, and the picker. Then run vitest, tsc, eslint and prettier on the changed files

## 7. Verification

- [x] 7.1 Run the web-api and ai-api suites in full
- [ ] 7.2 With the user's go-ahead:
  - [ ] 7.2.1 Import the real Open CEDA workbook and match one company's lines
  - [ ] 7.2.2 Review the 20 largest-emission lines' sectors for plausibility, and compare the agent's matches with the fallback's
  - [ ] 7.2.3 Check that the emissions card's estimated spend agrees with the coverage card's posted spend under the same filters
- [ ] 7.3 Browser check of Spend Lines at desktop and phone width: the card doesn't shift the layout, the column fits without horizontal scroll, and the picker works

## 8. Calculations and the dashboard

- [x] 8.1 Carry each line's calculation (spend share, rate, converted, factor, area, sector) through the estimate, and return it as `emission_calculation` on list and detail lines (tests)
- [x] 8.2 `GET /reports/spend-emissions`: period and comparison kg, twelve months, spend estimated per currency, top five sectors (tests)
- [ ] 8.3 Web: the calculation on hover of a line's CO₂e, and an emissions section in the line editor with sector, source, confidence, reasoning and the calculation (tests)
- [ ] 8.4 Web: the dashboard's emissions section (tests)
- [ ] 8.5 Browser check of the new pieces
