## 1. Data model and migration

- [x] 1.1 Models: `CompanyItem`, `Product`, `SpecComparison`, `MarketplaceQuery`, `MarketplaceOffer`, `ItemAlternative` (with review fields and `ref_key`), each in its own file; `PipelineRun.params`; `Organization.price_benchmark_enabled`
- [x] 1.2 Remove the `Recommendation` model, `Company.recommendations` and its deletion in `company_deletion.py`
- [x] 1.3 Migration `0023_cheaper_alternatives` creating the tables and columns, dropping `recommendations`, with a downgrade; the indexes the list and the searches need
- [x] 1.4 New run kinds `find_alternatives` and `scan_alternatives` in `PipelineRunKind`, the web types and the run labels
- [x] 1.5 Config: the `ALTERNATIVES_*`, `BENCHMARK_MIN_ORGANIZATIONS`, `SEARXNG_URL`, `ALTERNATIVES_PAGES_PER_ITEM`, `ALTERNATIVES_HOST_INTERVAL_S` and distributor key settings with defaults, documented in `.env.example`
- [x] 1.6 A `searxng` service in `docker-compose.yml` on port 8888 with a mounted `settings.yml` (JSON format on, limiter off), and `SEARXNG_URL` in `.env.example`

## 2. Stored items and unit prices (ai-api)

- [x] 2.1 `items/stored.py`: refresh `company_items` from the item grouping page by page: text, supplier, category, 12-month spend; keep the specification and product
- [x] 2.2 Pricing units and the line-unit table (stk, kg, m, l, rulle, pk…), with tests
- [x] 2.3 Unit price and yearly quantity per item from `base_amount` and `quantity × units per line unit`, also in EUR, with the reason when there is none (tests: cable box, missing quantity)

## 3. Specifications (ai-api)

- [x] 3.1 `specs/` package: the `Specification` and `Attribute` models, the reply models, and `SPEC_VERSION`
- [x] 3.2 The extraction prompt (class rule, product type, pricing units, numeric attributes with direction and unit, tiered attributes with family, tier and generation) and batched extraction with one-by-one retry, as the agreement judge does (tests with a stub model)
- [x] 3.3 Extract only items without a specification or whose text hash or version changed; never overwrite a person's; count failures and retry later (tests)
- [x] 3.4 Identifier normalisation and product linking by GTIN and by brand and part number (tests: one keyboard, two suppliers)
- [x] 3.5 The global `item_specs` Qdrant index: ensure and search, filtered by organization, class and pricing unit; degrade when Qdrant is down (tests with the in-memory client)

## 4. Matching and prices (ai-api)

- [x] 4.1 The exact match by identifiers (tests)
- [x] 4.2 Attribute unit conversion and the numeric comparison by direction; a missing attribute rejects (tests: 8 GB against 16 GB, mm against cm)
- [x] 4.3 `tiers.py`: the ordered tier families (Intel Core, Core Ultra, Ryzen, Apple M, EN 10025 steel grades), the part parser for family, tier and generation, and the comparison: a lower tier is worse whatever the generation, an older generation is worse (tests: i3 and i5 against i7, 11th against 13th generation i7, Ultra 7 against i7)
- [x] 4.4 The LLM decisions: product type pairs, tiered parts the table can't place (conservative, uncertain is worse) and the other attributes, batched per item and cached in `spec_comparisons` (tests: S355J2 against S235JR, Ryzen 7 against i7, a tablet against a laptop)
- [x] 4.5 Standard VAT rates by country, the conversion to a price per pricing unit, without VAT, in base currency, and the saving threshold (tests: a webshop price with VAT, too small a saving)
- [x] 4.6 The yearly saving and the per-attribute comparison stored on the alternative

## 5. Sources (ai-api)

- [x] 5.1 History: same product and similar specifications within the organization, cheaper, with supplier, company and last date (tests)
- [x] 5.2 Benchmark: per-organization prices by product and by specification signature, taking-part organizations only, at least three besides the viewer, median and lowest quartile in the viewer's currency, nothing that names anyone (tests: too few, opted out)
- [x] 5.3 The `OfferSource` interface, `Offer` with price breaks, the per-provider rate limiter, the shared query and offer cache with expiry, and offers normalised to specifications by the extraction prompt (tests)
- [x] 5.4 Product page reading: Crawl4AI fetch with the robots check, per-host interval and timeout; schema.org Product/Offer from JSON-LD and microdata first; the LLM only for missing attributes or pages without structured data (tests with saved pages)
- [x] 5.5 Shop-search connector: `shops.yaml` per market with search URL templates and product hosts, results page crawled for product links, identifier query then attribute query (tests with saved pages)
- [x] 5.6 Distributor connectors: Farnell, Mouser and Digi-Key clients (RS left out: no public API specification), keyword search, price breaks at the item's typical order quantity (tests with recorded responses)
- [x] 5.7 Open-web connector: the `SearchProvider` interface with SearXNG (JSON API, market language) as default and DuckDuckGo as fallback, the block list, found product pages read as in 5.4 (tests with a stub search)
- [x] 5.8 A failing connector is logged, counted and skipped for the rest of the run (tests)
- [x] 5.9 Agreement conflicts: preferred-supplier and behind commitments from the item's in-scope rulings (tests)

## 6. Searching and runs (ai-api)

- [x] 6.1 `alternatives/search.py`: one item's search across the enabled sources, replacing its open alternatives per source, keeping reviewed ones and skipping dismissed refs (tests)
- [x] 6.2 The `find_alternatives` executor: extract the item's specification first when missing; a summary per source
- [x] 6.3 The `scan_alternatives` executor: refresh items, extract due specifications, update the index, and search the due items by spend up to the limit (tests)
- [x] 6.4 The worker tick queues a scan per company when `ALTERNATIVES_SCAN_ENABLED` is set and the interval has passed, below agreements and documents
- [x] 6.5 Remove `procurement_agent`, `redundancy` and their calls in `sync/runner.py`, renumbering the sync's steps

## 7. web-api

- [x] 7.1 Schemas for items, specifications, alternatives and their list
- [x] 7.2 `GET /alternatives`: items with an open alternative, best saving first, with filters by company, source, match and class, paging, and the total (tests)
- [x] 7.3 `GET /items/{id}`: specification, unit price or the reason for none, alternatives, last search and a running one (tests)
- [x] 7.4 `PATCH /items/{id}/specification` for managers, audited, marking the item for a new search (tests)
- [x] 7.5 `POST /items/{id}/find-alternatives` for managers, reusing a queued run (tests)
- [x] 7.6 `PATCH /alternatives/{id}` to dismiss with a reason and note, mark switched or reopen, audited (tests)
- [x] 7.7 A line's item (`GET /invoice-lines/{id}/item`, `POST /invoice-lines/{id}/find-alternatives` storing the item when needed) and the line's `item_key`; the organization endpoint gets `price_benchmark_enabled`, settable by org admins and audited (tests)
- [x] 7.8 Delete a company's items and alternatives in `company_deletion.py`

## 8. Web

- [x] 8.1 API types and query and mutation options for alternatives, items and the benchmark setting
- [x] 8.2 The Alternatives page: the sidebar entry, list, filters, paging, total and empty states (tests)
- [x] 8.3 The item page: specification, unit price, alternatives with attributes side by side, origin, agreement notes, search status (tests)
- [x] 8.4 Specification editing for managers (tests)
- [x] 8.5 The Find cheaper alternatives action on the item page and in the spend-line drawer, with the running state (tests)
- [x] 8.6 Review actions: dismiss with reason and note, mark switched, reopen; viewers see no actions (tests)
- [x] 8.7 The price benchmark toggle in the organization settings (tests)

## 9. Verification

- [ ] 9.1 Run the ai-api, web-api and web suites, and tsc
- [ ] 9.2 A real-model sample: extract specifications for 100 items of the test companies (materials, parts and finished goods) and check the class, pricing unit and pack size by hand; record accuracy in `design.md`
- [ ] 9.3 With the user's go-ahead: run the migration on dev, search a few items on request (a laptop, a cable box, toilet paper, a steel bar), and check the alternatives, tiers and prices against the offers
