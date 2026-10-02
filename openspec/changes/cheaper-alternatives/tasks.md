## 1. Data model and migration

- [ ] 1.1 Models: `CompanyItem`, `Product`, `SpecComparison`, `MarketplaceQuery`, `MarketplaceOffer`, `ItemAlternative` (with review fields and `ref_key`), each in its own file; `PipelineRun.params`; `Organization.price_benchmark_enabled`
- [ ] 1.2 Remove the `Recommendation` model, `Company.recommendations` and its deletion in `company_deletion.py`
- [ ] 1.3 Migration `0023_cheaper_alternatives` creating the tables and columns, dropping `recommendations`, with a downgrade; the indexes the list and the searches need
- [ ] 1.4 New run kinds `find_alternatives` and `scan_alternatives` in `PipelineRunKind`, the web types and the run labels
- [ ] 1.5 Config: the `ALTERNATIVES_*`, `BENCHMARK_MIN_ORGANIZATIONS`, `SHOPPING_SEARCH_PROVIDER` and connector key settings with defaults, documented in `.env.example`

## 2. Stored items and unit prices (ai-api)

- [ ] 2.1 `items/stored.py`: refresh `company_items` from the item grouping page by page: text, supplier, category, 12-month spend; keep the specification and product
- [ ] 2.2 Pricing units and the line-unit table (stk, kg, m, l, rulle, pk…), with tests
- [ ] 2.3 Unit price and yearly quantity per item from `base_amount` and `quantity × units per line unit`, also in EUR, with the reason when there is none (tests: cable box, missing quantity)

## 3. Specifications (ai-api)

- [ ] 3.1 `specs/` package: the `Specification` and `Attribute` models, the reply models, and `SPEC_VERSION`
- [ ] 3.2 The extraction prompt (class rule, product type, pricing units, numeric attributes with direction and unit, tiered attributes with family, tier and generation) and batched extraction with one-by-one retry, as the agreement judge does (tests with a stub model)
- [ ] 3.3 Extract only items without a specification or whose text hash or version changed; never overwrite a person's; count failures and retry later (tests)
- [ ] 3.4 Identifier normalisation and product linking by GTIN and by brand and part number (tests: one keyboard, two suppliers)
- [ ] 3.5 The global `item_specs` Qdrant index: ensure and search, filtered by organization, class and pricing unit; degrade when Qdrant is down (tests with the in-memory client)

## 4. Matching and prices (ai-api)

- [ ] 4.1 The exact match by identifiers (tests)
- [ ] 4.2 Attribute unit conversion and the numeric comparison by direction; a missing attribute rejects (tests: 8 GB against 16 GB, mm against cm)
- [ ] 4.3 `tiers.py`: the ordered tier families (Intel Core, Core Ultra, Ryzen, Apple M, EN 10025 steel grades), the part parser for family, tier and generation, and the comparison: a lower tier is worse whatever the generation, an older generation is worse (tests: i3 and i5 against i7, 11th against 13th generation i7, Ultra 7 against i7)
- [ ] 4.4 The LLM decisions: product type pairs, tiered parts the table can't place (conservative, uncertain is worse) and the other attributes, batched per item and cached in `spec_comparisons` (tests: S355J2 against S235JR, Ryzen 7 against i7, a tablet against a laptop)
- [ ] 4.5 Standard VAT rates by country, the conversion to a price per pricing unit, without VAT, in base currency, and the saving threshold (tests: a webshop price with VAT, too small a saving)
- [ ] 4.6 The yearly saving and the per-attribute comparison stored on the alternative

## 5. Sources (ai-api)

- [ ] 5.1 History: same product and similar specifications within the organization, cheaper, with supplier, company and last date (tests)
- [ ] 5.2 Benchmark: per-organization prices by product and by specification signature, taking-part organizations only, at least three besides the viewer, median and lowest quartile in the viewer's currency, nothing that names anyone (tests: too few, opted out)
- [ ] 5.3 The `OfferSource` interface, `Offer` with price breaks, the per-provider rate limiter, the shared query and offer cache with expiry, and offers normalised to specifications by the extraction prompt (tests)
- [ ] 5.4 Shopping-search connector: SerpApi Google Shopping behind a provider interface, the market's country and language, identifier query then attribute query, the product page read for cheaper candidates without attributes (tests with recorded responses)
- [ ] 5.5 Distributor connectors: RS, Farnell, Mouser and Digi-Key clients, part number then keyword, price breaks at the item's typical order quantity (tests with recorded responses)
- [ ] 5.6 Open-web connector (off by default): DDG search, Crawl4AI with the robots check, per-host interval, the LLM reading page offers (tests with stub search, fetch and model)
- [ ] 5.7 A failing connector is logged, counted and skipped for the rest of the run (tests)
- [ ] 5.8 Agreement conflicts: preferred-supplier and behind commitments from the item's in-scope rulings (tests)

## 6. Searching and runs (ai-api)

- [ ] 6.1 `alternatives/search.py`: one item's search across the enabled sources, replacing its open alternatives per source, keeping reviewed ones and skipping dismissed refs (tests)
- [ ] 6.2 The `find_alternatives` executor: extract the item's specification first when missing; a summary per source
- [ ] 6.3 The `scan_alternatives` executor: refresh items, extract due specifications, update the index, and search the due items by spend up to the limit (tests)
- [ ] 6.4 The worker tick queues a scan per company when `ALTERNATIVES_SCAN_ENABLED` is set and the interval has passed, below agreements and documents
- [ ] 6.5 Remove `procurement_agent`, `redundancy` and their calls in `sync/runner.py`, renumbering the sync's steps

## 7. web-api

- [ ] 7.1 Schemas for items, specifications, alternatives and their list
- [ ] 7.2 `GET /alternatives`: items with an open alternative, best saving first, with filters by company, source, match and class, paging, and the total (tests)
- [ ] 7.3 `GET /items/{id}`: specification, unit price or the reason for none, alternatives, last search and a running one (tests)
- [ ] 7.4 `PATCH /items/{id}/specification` for managers, audited, marking the item for a new search (tests)
- [ ] 7.5 `POST /items/{id}/find-alternatives` for managers, reusing a queued run (tests)
- [ ] 7.6 `PATCH /alternatives/{id}` to dismiss with a reason and note, mark switched or reopen, audited (tests)
- [ ] 7.7 The line read gets its `item_id`; the organization endpoint gets `price_benchmark_enabled`, settable by org admins and audited (tests)
- [ ] 7.8 Delete a company's items and alternatives in `company_deletion.py`

## 8. Web

- [ ] 8.1 API types and query and mutation options for alternatives, items and the benchmark setting
- [ ] 8.2 The Alternatives page: the sidebar entry, list, filters, paging, total and empty states (tests)
- [ ] 8.3 The item page: specification, unit price, alternatives with attributes side by side, origin, agreement notes, search status (tests)
- [ ] 8.4 Specification editing for managers (tests)
- [ ] 8.5 The Find cheaper alternatives action on the item page and in the spend-line drawer, with the running state (tests)
- [ ] 8.6 Review actions: dismiss with reason and note, mark switched, reopen; viewers see no actions (tests)
- [ ] 8.7 The price benchmark toggle in the organization settings (tests)

## 9. Verification

- [ ] 9.1 Run the ai-api, web-api and web suites, and tsc
- [ ] 9.2 A real-model sample: extract specifications for 100 items of the test companies (materials and finished goods) and check the class, pricing unit and pack size by hand; record accuracy in `design.md`
- [ ] 9.3 With the user's go-ahead and API keys: run the migration on dev, search a few items on request (a laptop, a cable box, toilet paper, a steel bar), and check the alternatives, tiers and prices against the offers
