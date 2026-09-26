## 1. Data model

- [ ] 1.1 Add `EmissionFactorSet`, `EmissionSector` and `EmissionFactor` models (one file each under `db/models/`) with the uniques from the design, and export them
- [ ] 1.2 Add `emission_sector_id`, `emission_sector_source` (`EmissionSectorSource` enum: ai, human) and `emission_sector_confidence` to `InvoiceLine`
- [ ] 1.3 Add `MATCH_EMISSIONS = "match_emissions"` to `PipelineRunKind`
- [ ] 1.4 Write migration `0017_emissions` (the tables, the line columns, and the run kind if it is a DB enum); downgrade drops them. Do not run it
- [ ] 1.5 Make company deletion leave factor sets and sectors alone (they are global), and cover it with a test

## 2. Factor sets and import (web-api)

- [ ] 2.1 Confirm the Open CEDA workbook's layout, sheet, headers, dollar year, price basis and GWP basis from a downloaded copy (ask the user for the file); record them in the importer's column spec and the design's open questions
- [ ] 2.2 `web_api/emissions/countries.py`: map the workbook's country names to ISO alpha-2 codes, reporting unmapped ones (tests)
- [ ] 2.3 `web_api/emissions/import_factors.py`: read the workbook by header names with `openpyxl`, upsert sectors, replace the version's factors, `--activate` deactivating the rest in one transaction, and print the counts. Tests with a small generated workbook: happy path, a missing column, a duplicate factor, a re-import. Ask the user to add `openpyxl` to web-api
- [ ] 2.4 `web_api/emissions/factors.py`: `active_factor_set(session)` and `factor_for(session, set, sector_id, countries)` returning the factor and the country used, with the fallback order (tests)

## 3. Estimate (web-api)

- [ ] 3.1 Move `split` out of `spend_analytics/allocation.py` into a shared module both packages import, and keep allocation's behaviour and tests unchanged
- [ ] 3.2 `web_api/emissions/estimate.py`:
  - [ ] 3.2.1 Split a voucher's net spend across its lines, absorbing discounts
  - [ ] 3.2.2 Convert to the set's currency at the voucher date through `FxService`
  - [ ] 3.2.3 Multiply by the factor, with the supplier country taken from the vendor, else the printed country, else the company
  - [ ] 3.2.4 Return per-line kg, the country used, and the voucher's total and `emissions_status`
- [ ] 3.3 Tests on the `Books` builder:
  - [ ] 3.3.1 Single line; posted net vs VAT-inclusive lines; discount absorbed
  - [ ] 3.3.2 Partial; `no_lines`; `unmatched`; `no_factor`; `unconverted` (stub provider failing); `no_factor_set`
  - [ ] 3.3.3 Country fallback
- [ ] 3.4 Batch the lookups for a page of vouchers: one query for the lines' sectors and factors, and rates memoized per (currency, date)

## 4. API (web-api)

- [ ] 4.1 Add the emissions fields to `VoucherGroupRead` and `InvoiceLineRead`, and fill them in `list_voucher_groups`
- [ ] 4.2 `GET /erp-entries/vouchers/emissions`: same filters and scoping as `/summary`, returning the factor set, the total, spend per currency and counts per status (schema in `schemas/erp/`)
- [ ] 4.3 `GET /emission-sectors?q=&limit=`: a new router, searching the active classification (limit default 20, max 50)
- [ ] 4.4 `PATCH /invoice-lines/{id}` accepts `emission_sector_id`:
  - [ ] 4.4.1 A sector sets source `human`; null clears; a sector of another classification gets 422
  - [ ] 4.4.2 Audited
  - [ ] 4.4.3 Editing item name, description or category clears an `ai` sector
- [ ] 4.5 API tests for 4.1–4.4, including tenant scoping and the no-factor-set case
- [ ] 4.6 Accept `match_emissions` in `POST /companies/{id}/runs` (test)

## 5. Sector matching (ai-api)

- [ ] 5.1 `ai_api/emissions/sector_index.py`: build and query a Qdrant collection per classification from `emission_sectors`, reusing the `rag/indexer` helpers and an injectable `embed_fn` (tests with a fake embedder)
- [ ] 5.2 `ai_api/emissions/prompt.py` and `choice.py`: the numbered-candidate prompt and the pydantic answer (number or none, plus confidence) parsed with `json_repair`, without guided decoding (tests for none, out-of-range and malformed answers)
- [ ] 5.3 Sector-match cache, following `persistence/categorization_cache`: keyed by question, offered-sector hash and classification (tests)
- [ ] 5.4 `ai_api/emissions/lines.py` `match_company(session, company_id, *, limit, rematch, complete, retrieve)`:
  - [ ] 5.4.1 Select the eligible lines and build each query from the line, category path, supplier description and country
  - [ ] 5.4.2 Retrieve 12 candidates, then use the cache or the LLM
  - [ ] 5.4.3 Store the result with source `ai`, never touching `human` lines
  - [ ] 5.4.4 Return the counts, and skip when no set is active
- [ ] 5.5 Tests for `match_company`: human lines untouched, re-match on a new classification, cache hits counted, `--rematch` clears only `ai`
- [ ] 5.6 `ai_api/emissions/runner.py` CLI (`--company-id`, `--limit`, `--rematch`), and a `match_emissions` executor in `worker/executors.py` (tests)

## 6. Frontend

- [ ] 6.1 Types and queries:
  - [ ] 6.1.1 Emissions fields on vouchers and lines
  - [ ] 6.1.2 `voucherEmissionsQueryOptions` (keyed on the filters, `keepPreviousData`) and `emissionSectorsQueryOptions`
  - [ ] 6.1.3 `emission_sector_id` on the line update
  - [ ] 6.1.4 `match_emissions` in the run kinds and labels
- [ ] 6.2 `formatEmissions(kg)`: kg below 1,000, t with one decimal above, at most 3 significant figures (tests)
- [ ] 6.3 `components/entries/summary/emissions-card.tsx`:
  - [ ] 6.3.1 Total, share estimated per currency, method line and attribution
  - [ ] 6.3.2 Not-estimated counts with reasons
  - [ ] 6.3.3 Its own loading, error and retry states, fixed height, and the no-factor-set state
  - [ ] 6.3.4 Placed beside the coverage card in `entries-panel.tsx`
- [ ] 6.4 A CO₂e column in the voucher table (partial mark, "—" with reason). Each expanded line shows its sector with an AI/human mark, a needs-review mark below the threshold, its CO₂e, and the factor country on hover and focus
- [ ] 6.5 An emission sector picker in the line editor: a debounced server search, name and code shown, clearable, disabled with an explanation when no set is active; saving invalidates the voucher list and the emissions summary
- [ ] 6.6 Component tests for the card, the column and line display, and the picker. Then run vitest, tsc, eslint and prettier on the changed files

## 7. Verification

- [ ] 7.1 Run the web-api and ai-api suites in full
- [ ] 7.2 With the user's go-ahead:
  - [ ] 7.2.1 Import the real Open CEDA workbook and match one company's lines
  - [ ] 7.2.2 Review the 20 largest-emission lines' sectors for plausibility
  - [ ] 7.2.3 Check that the emissions card's estimated spend agrees with the coverage card's posted spend under the same filters
- [ ] 7.3 Browser check of Spend Lines at desktop and phone width: the card doesn't shift the layout, the column fits without horizontal scroll, and the picker works
