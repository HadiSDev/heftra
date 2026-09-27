## Context

**What Spend Lines already has.** Spend Lines (`routes/_authed/invoice-lines.tsx`, `components/entries/`) lists vouchers with their postings and invoice lines, and shows a coverage card fed by `GET /erp-entries/vouchers/summary`. Those figures rest on three things:

- A voucher's spend is its net expense posting in the company's base currency (`vouchers/amounts.voucher_amount`).
- The lines split that spend by their share of `base_amount`: `spend_coverage.categorized_share` for the card, `spend_analytics.allocation.split` for the dashboard. `split` works in exact cents, and an uncategorized negative line (a discount) is absorbed by the others.
- Lines carry a spend category from their org's tree (`spend_category_id` and `level_1…4`). Suppliers carry `country_code`, and invoices carry `document_supplier_country_code` as printed.

**The rest of the stack we build on:**

- **Categorization** (ai-api) is retrieve-then-choose. It embeds the org's tree into Qdrant (`rag/indexer`), narrows candidates (`sync/categorizer.build_candidates_from_retrieval`), and lets the local LLM pick a numbered candidate with a confidence, parsed with `parse_model`. Answers are cached by a question key and a hash of the candidates offered (`persistence/categorization_cache`).
- **FX** converts through EUR with a DB rate cache (`fx/service.FxService.get_rate(from, to, on_date)`).
- **Runs**: the worker executes `PipelineRun` kinds from `worker/executors.EXECUTORS`.
- **Data sharing**: ai-api writes to the shared database through web-api's models; web-api never imports ai-api.

**Nothing about emissions exists yet.**

**The factor source.** Open CEDA 2025 (`Open CEDA 2025 by Watershed.xlsx`, public at `s3://open-ceda/data/`, released 2025-11-11, CC BY-SA 4.0) was inspected. Its sheets:

- **`GHG_t_Raw`**: the base factors in kgCO₂e per 2023 USD at producer price. There are 400 sectors, keyed by BEA codes such as `541511`, with names in the row above the codes. There are 149 countries, keyed by ISO 3166 alpha-3 codes, with no blank cells.
- **`GHG_t`**: the same factors re-expressed through the Cover sheet's currency and year selectors, so its cached values depend on how the file was last saved. We don't read it.
- **`Purchaser - producer conversion`**: a BEA ratio per sector, between 0.47 and 0.99. It gives the producer value of one dollar paid by a purchaser.
- **`Regional Average EFs`**: 21 UN-subregion averages in the same unit.
- **`Country to region mapping`**: 250 ISO alpha-3 codes, each mapped to its subregion.
- **`Metadata`**: each sector's code, name and a paragraph of description.
- **`Sector level Price Index`**: 2018–2024, with 2023 = 100.

The attribution text requires "CEDA by Watershed" wherever calculations are shown.

## Goals / Non-Goals

**Goals:**
- A defensible spend-based kgCO₂e per line and per voucher that agrees with the spend Spend Lines already shows.
- Each line matched to the most specific sector the evidence supports, correctable by a human, with the AI never overwriting a human.
- A factor source that can be replaced or updated by importing a new set, without touching code.
- Honest coverage: say how much spend was estimated and why the rest wasn't.

**Non-Goals:**
- Dashboard emission tiles and trends. They are a follow-up that reuses the same estimate.
- Activity-based factors (litres, kWh, km), supplier-specific or primary data, and market-based electricity.
- Inflation adjustment of spend to the factor's price year. The price year is shown instead.
- EXIOBASE through pymrio. The factor-set model is generic enough to take it later if a licence allows.
- Purchaser-to-basic price margin handling beyond what the factor set itself embodies.

## Decisions

### Open CEDA as the first factor set, behind a generic factor-set model
Four tables:
- `emission_factor_sets`: id, source, version, classification, currency, price_year, price_basis, licence, attribution, imported_at, active.
- `emission_sectors`: id, classification, code, name, description, unique on (classification, code).
- `emission_factors`: factor_set_id, sector_id, `country_code` or `region` (exactly one set, by a check constraint), kg_co2e_per_unit as Numeric(18, 8), unique on (set, sector, country, region).
- `emission_country_regions`: factor_set_id, country_code, region.

Country codes are stored as ISO alpha-2, which is what vendors and companies carry.

Sectors belong to a classification rather than a set. A new release of the same classification keeps line matches valid; a set on a different classification makes lines re-match. Exactly one set is active: importing with `--activate` deactivates the others in the same transaction.

**Alternatives considered:**
- **Climatiq API.** Per-call cost, factors not stored, and a network dependency on every read.
- **EXIOBASE 3.10 via pymrio.** Licensed for non-commercial use only.
- **EXIOBASE 3.8.2 via pymrio.** CC BY-SA, but real data ends in 2011, with GB-scale downloads and a matrix inversion to run.
- **EPA USEEIO.** US only.

### Importer as a web-api CLI
`python -m web_api.emissions.import_factors --file <openceda.xlsx> [--activate]` reads the workbook with `openpyxl` (read-only, values only) and writes everything in one transaction. It is idempotent: importing the same version again replaces that set's factors. It reads:

- **The set's fields:** version from the Cover sheet's "Version" cell, and year, price type and currency from the header rows of `GHG_t_Raw`.
- **Sectors:** from `Metadata`, including their descriptions.
- **Country factors:** from `GHG_t_Raw`.
- **Region factors:** from `Regional Average EFs`.
- **The country-to-region map:** from `Country to region mapping`.

Sheets and header cells are found by their names and labels, not by position. If an expected sheet or label is missing, it fails with a message naming it.

**Purchaser prices.** Our spend is what the company paid, a purchaser price, while CEDA's factors are per producer-price dollar. The importer multiplies each factor by its sector's purchaser-to-producer ratio and stores the result with `price_basis = "purchaser"`. The estimate then needs no margin logic.

**Country codes.** Alpha-3 codes are turned into alpha-2 through a static ISO 3166 table in `web_api/emissions/countries.py`. We use a static table because no country library is installed, and the list is stable. A code the table doesn't know is reported and skipped. A local check against the real workbook confirms every code it holds is known.

The file is not committed to the repo. The user downloads it (the licence stays with the file) and runs the import, as with the other runners.

### Match at line level, not category level
A spend category is too coarse to pick a factor from. "Direct Costs / Cost of Goods Sold" covers groceries and server hardware alike; "Technology / Hardware" covers laptops (manufacturing) and repairs (services). Each line is therefore matched to a sector using:

- its item name and description;
- its spend category path;
- the supplier's name, its enrichment description and its country.

The spend category is a strong hint, not the key. Alternative considered: a static map from the default template's leaves to sectors. Rejected because custom trees would have no map and the template's leaves are too broad. Its idea survives as the category path in the prompt.

**An agent with tools, falling back to a single choice.** The matcher is the first CrewAI agent here that uses tools, an "Emission Sector Analyst". It is told the line (item name, description, amount), its spend category path, and the supplier's name and country, and it gets four tools:

- `search_sectors(query)`: the 8 sectors closest to a free-text query, each with code, name and the first sentence of its description. It searches a Qdrant collection per classification, embedding name plus description with the same embedding and helpers as the tree index.
- `sector_details(code)`: a sector's full description, to tell apart near neighbours such as "Software publishers" and "Custom computer programming services".
- `supplier_profile()`: the supplier's enrichment description and website, as stored on the vendor.
- `other_lines()`: the other lines of the same invoice, as context for a line that says only "Service fee".

It may search several times with its own wording, which a single embedding query can't do. For example, "Hetzner AX41" becomes a search for "data center hosting". It must answer in JSON with:
- `code`: a code it saw in a tool result;
- `confidence`: 0–1;
- `rationale`: one sentence.

Its budget is bounded: `max_iter=6` and the configured LLM timeout.

**Fallback.** With a 4B local model, tool use will sometimes fail: a malformed tool call, a hit iteration limit, a timeout, or a code that isn't in the classification. In each of those cases the matcher falls back to the single-shot path. That path retrieves the top 12 sectors for the line's text, category and supplier description, and the LLM picks a number with a confidence, or answers "none". The run summary counts agent answers and fallback answers apart, so their quality can be compared. Both paths use prompt-for-JSON parsed with `json_repair` and pydantic, not guided decoding, as elsewhere. The agent's model and prompts live in `ai_api/emissions/agent/`, one module per concern (tools, prompt, answer), and the fallback in `ai_api/emissions/choice/`.

**Low confidence is suggested, not withheld.** Every match is stored with its confidence and rationale. Below `CATEGORIZATION_REVIEW_THRESHOLD`, the line is shown as needing review, the way a low-confidence category is. Only "none fits" leaves a line unmatched.

**Cache.** A persisted cache keyed on (question key, classification) means identical lines, such as monthly subscriptions, cost one run. The question key covers the line text, category path and supplier. The agent picks its own candidates, so there is no candidate-set hash.

**Stored on the line.** Three new columns:
- `emission_sector_id`: FK to `emission_sectors`, nullable.
- `emission_sector_source`: `ai` or `human`.
- `emission_sector_confidence`: Numeric(4,3), nullable.
- `emission_sector_rationale`: text, nullable.

A human choice sets the source to `human` and clears the confidence. The matcher only ever touches lines with no sector, or whose source is `ai` and whose classification differs from the active set's.

**Invalidation.** A human edit to a line's item name, description or spend category clears an `ai` sector, so the next run re-matches it. A `human` sector is kept.

### Estimate on read, from the same netting as Spend Lines
`web_api/emissions/estimate.py` works as follows:

1. **Split.** It takes a voucher's rows and its lines and splits the voucher's net base-currency spend across the lines. This reuses `split(amount, weights)` with line ids as keys, with the same absorbed-discount rule.
2. **Convert.** It converts each line's share to the set's currency with `FxService.get_rate(base, set.currency, spent_on)`. The voucher date is the one allocation uses: the earliest expense posting.
3. **Multiply.** It multiplies by the factor for (sector, country).

**Country fallback.** The supplier's country is the vendor's `country_code`, else the invoice's `document_supplier_country_code`. The factor is looked up in this order:
1. The supplier's country.
2. The supplier's country's UN subregion average.
3. The company's country.
4. The company's subregion.
5. The rest-of-world average: `GHG_t_Raw`'s `ROW` row, stored as the region "Rest of World".

A supplier country in none of CEDA's 149 countries still gets its region: Taiwan maps to "Eastern Asia", for instance.

The country actually used is returned, so the UI can say "factor for DE" or "factor for Eastern Asia".

**What can't be estimated** is reported per voucher, with one reason each:
- `no_lines`: journal-only vouchers.
- `unmatched`: lines have no sector yet, or the matcher said none fits.
- `no_factor`: no factor for any country tried.
- `unconverted`: no FX rate.

A voucher with only some lines matched is estimated for those lines' share, and the rest is counted as unmatched spend.

Nothing is persisted, so a correction, a re-categorized line, a new FX rate or a new factor set shows at once. Alternative considered: storing kgCO₂e per line in a batch job. Rejected because it duplicates the netting, goes stale on every edit, and the volumes (tens to low thousands of vouchers) make on-read computation cheap.

### API shape
- `GET /erp-entries/vouchers`:
  - each voucher gains `kg_co2e` (null when nothing could be estimated) and `emissions_status` (`estimated`, `partial`, or one of the reasons);
  - each `InvoiceLineRead` gains `emission_sector` (`{id, code, name}`), `emission_sector_source`, `emission_sector_confidence`, `kg_co2e` and `emission_area`.
- `GET /erp-entries/vouchers/emissions` takes the same filters as `/summary` and returns:
  - `factor_set`: source, version, price year, currency, attribution; null if no set is active;
  - a total `kg_co2e`;
  - per base currency, `posted_spend` and `estimated_spend`;
  - voucher counts per reason.

  It is a separate endpoint so a slow FX lookup can't hold up the coverage card, and each can fail on its own. The same reason kept the dashboard's endpoints separate.
- `GET /emission-sectors?q=&limit=` searches the active set's classification by code or name, for the picker.
- `PATCH /invoice-lines/{id}` accepts `emission_sector_id` (a sector id or null). It is audited like other line edits. A sector outside the active classification gets `422`.

### Runs
- New `PipelineRunKind.MATCH_EMISSIONS = "match_emissions"`, executed by `ai_api.emissions.lines.match_company(session, company_id)`, whose summary is `{matched, unmatched, cached, failed}`.
- The same function backs `python -m ai_api.emissions.runner --company-id <id> [--limit N] [--rematch]`. `--rematch` clears the company's `ai` sectors first.
- With no active factor set, the run succeeds with `{skipped: "no active factor set"}` rather than failing.
- Matching is not chained into sync yet. Once quality is proven on real data, the sync's categorization step can call it.

### Units and display
The API returns kg with 3 decimals. The UI shows:
- `kg CO₂e` below 1,000;
- `t CO₂e` with one decimal above that;
- "—" with the reason on hover when nothing was estimated.

The emissions card carries a method line such as "Spend-based estimate · Open CEDA 2025 · 2023 USD" and the attribution "CEDA by Watershed", as the licence requires.

## Risks / Trade-offs

- **[Spend-based factors are averages; a precise-looking number misleads]** → The card is labelled an estimate, shows the method and price year, and rounds to meaningful precision. Values are never shown to more than 3 significant figures in tiles.
- **[Wrong sector match inflates or deflates by 10×]** → The confidence is stored. Low-confidence matches (below the categorization review threshold) are marked like needing review, and a human can correct them in one picker. The top sectors by emissions are what a reviewer should check first. The drawer shows the sector and country used.
- **[No inflation adjustment]** → Spend is 2024–2026 money against 2023 USD factors, so estimates run a few percent high. Accepted and stated in the method line; a deflator can be added to the estimate without schema change.
- **[FX lookups on read]** → They go through FxService's DB cache. A cold date fetches once, then it's cached. A failed fetch marks the voucher `unconverted` rather than failing the page.
- **[Workbook layout changes between releases]** → The importer finds columns by header name, fails loudly on a missing column, and reports counts.
- **[Licence: CC BY-SA share-alike on derived factor data]** → We redistribute nothing. Factors stay in our DB and are shown with attribution. Exporting factor tables to customers would need share-alike terms; that is out of scope.
- **[400 BEA sector names are terse for retrieval]** → Retrieval uses name plus code. If recall is poor on real data, a description column (generated once, offline) can be added to `emission_sectors` and embedded instead.

## Migration Plan

1. Migration `0017_emissions`: the three tables and the three line columns, all nullable. The downgrade drops them.
2. The user installs `openpyxl` in web-api, downloads the Open CEDA workbook, and runs `python -m web_api.emissions.import_factors --file … --version … --activate`.
3. The user runs `python -m ai_api.emissions.runner --company-id …`, or queues `match_emissions` from Settings.
4. Rollback: the UI shows "No emission factors imported" when no set is active, so deactivating the set hides every figure without a deploy.

## Open Questions

- The price index could deflate spend to 2023 dollars per sector, since the workbook carries it for 2018–2024. It is left out for now, and the method line states "2023 USD".
- Whether the agent path beats the single-shot path on real lines. The run summary separates them, and task 7.2 compares them.
