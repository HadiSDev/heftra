## Context

Spendyard knows what each company buys: lines are grouped into items by `item_key` (name, description, unit, category and supplier), with spend and an embedding per company in Qdrant (`spend-item-index`). The worker can call the LLM (`Ask = Callable[[str], str]`, prompt-for-JSON parsed with `parse_model`), search the web with keyless DDG (`web_context.ddg_search`), and crawl pages with Crawl4AI, which checks robots.txt (`enrichment/site/fetch.py`). Agreement analysis already judges items in numbered batches with a thread pool.

What is missing for alternatives:
- **Products.** The supplier is part of the item key, so the same keyboard from two suppliers is two items. Nothing links them.
- **Specifications.** There is nothing structured to compare: no grade, dimensions, memory or pack size.
- **A comparable price.** `Item.unit_price` is an unweighted average of `InvoiceLine.unit_price` in the invoice's currency. Only `amount` is converted to `base_amount`. A price per kg, metre or roll in base currency doesn't exist.
- **Cross-organization prices.** Vendors, the categorization cache and the web cache are shared across organizations, but no price data is.
- **Job parameters.** `pipeline_runs` has no parameters column, so a run can't name an item.
- **Throttling.** Nothing limits the rate of web requests.

There are also stubs to remove. The sync calls `procurement_agent.recommender` and `redundancy.detector`, which are empty, and the `recommendations` table has no router and no UI.

The product's users are procurement and finance people at small and mid-sized companies, mostly Danish for now (DKK, Danish-language item names). The model runs on one local GPU (gemma-4-E4B via vLLM), shared with categorization and agreement analysis.

## Goals / Non-Goals

**Goals:**
- An item specification and a price per pricing unit, for production materials and finished goods alike.
- Exact and equivalent alternatives from the organization's own purchases, other customers' anonymous prices and the open web, never worse on a key attribute.
- A yearly saving per alternative, items ranked by it, and the scan and on-request search.
- Bounded cost: LLM calls, searches and page reads per run are capped; everything that can be reused is cached.
- Prices shared between organizations only as anonymous aggregates of three or more.

**Non-Goals:**
- Ordering, requests for quotes or negotiating with suppliers.
- Shipping costs, minimum order quantities, lead times or stock in the price. They are shown when a page states them, but not included.
- Commodity price indices for materials (steel, copper, timber) and price forecasting. The existing `price-indices` capability can feed them later.
- Supplier catalogues or price lists uploaded by a person. That is a later source.
- Logged-in or B2B-only price portals, and marketplaces that need an account.
- Alternatives for services (consulting, rent, licences): they have no comparable unit. Items whose specification can't give a pricing unit are left out and say so.

## Decisions

### 1. Stored items, products and a global specification index

A `company_items` table gets one row per (company, item_key). It is refreshed with the same SQL grouping as `company_items()`, page by page. It holds:
- the item's text, supplier and category;
- the specification (JSON), who set it, a hash of the text it was read from, and the attempts left;
- the item's product;
- its 12-month spend, quantity in pricing units, and unit price in base currency and in EUR;
- when it was last searched.

A `products` table holds canonical products, unique by normalised EAN/GTIN and by normalised (brand, part number). Items link to a product when an identifier matches.

The specification index is one global Qdrant collection, `item_specs`:
- each point is an item, identified by `uuid5(company_id + item_key)`;
- its vector embeds the specification as text (product name, class, key attributes);
- its payload holds the organization, the company, the class, the pricing unit and the product.

One index serves both sources: history filters by organization, and the benchmark excludes it.

*Alternatives considered.*
- Per-company collections, as for agreements, can't search across organizations.
- Re-deriving items on every read is too slow for the Alternatives page's ranking.
- Matching products by name similarity alone is too loose for "exact".

### 2. Specification extraction in batches, keyed by the item's text

Specifications are read in numbered batches (`ALTERNATIVES_SPEC_BATCH`, default 8) with the agreement judge's pattern: thread pool, prompt-for-JSON, retry one by one on a bad batch. The prompt gives the class rule (bought by weight, length, area or volume, or to be processed, is `material`), the closed list of pricing units, and asks for key attributes with direction and unit, in English, snake_case names.

A specification is re-read only when the item's text hash or `SPEC_VERSION` changes, and never when a person set it. Line units are mapped to pricing units with a small deterministic table (stk/pcs/piece → piece, kg, m/meter/mtr → m, l/ltr, rulle → roll, pk/pakke → pack). The LLM supplies the pack size ("8 ruller", "305m kasse") as units per line unit.

The unit price is Σ `base_amount` ÷ Σ (`quantity` × units per line unit) over the last 12 months. A line without a quantity is excluded and counted.

*Alternatives considered.* Regex extraction of sizes and grades works only for a few patterns. Asking the model for the price per unit directly can't be checked.

### 3. Matching: exact by identifiers, equivalent by attributes, comparisons cached

The candidate pipeline for an item:
1. **Exact.** Same product, or the same GTIN, part number or brand and model. This is decided in code, after normalising: upper case, no spaces or hyphens.
2. **Same class and pricing unit,** or the candidate is dropped.
3. **Numeric attributes** are compared in code, after converting units with a small table (mm, cm, m; g, kg; GB, TB; W; V; in). The attribute's direction decides better or worse. A missing attribute rejects the candidate.
4. **Other attributes** are compared by the LLM in one batched prompt per item. For each pair it returns same, better or worse, with a reason. Any worse rejects the candidate.
5. **Comparisons are cached** in `spec_comparisons`, keyed by the two specification hashes and the version. The same pair is never asked twice, for any company.

*Alternatives considered.* LLM-only matching sometimes waves through less memory or a thinner ply, and the user asked never to show a worse product. A fully deterministic match can't tell that S355J2 is at least S235JR.

### 4. Sources

- **History.** Two queries over `company_items` of the same organization in the last 12 months: items with the same product, and the top `ALTERNATIVES_SIMILAR` hits from the specification index for the organization, class and pricing unit. Both are cheaper by the threshold. The alternative names the supplier, the company and the last purchase date.
- **Benchmark.** Per-organization prices for the item's product, or for items with the same **specification signature** (a hash of class, pricing unit and normalised key attributes), from organizations taking part other than the viewer's.
  - Each organization contributes its spend-weighted unit price in EUR, converted to the viewer's base currency.
  - Median and lowest quartile are computed in Python over at most a few hundred per-organization prices, never from line data.
  - The benchmark is shown only from at least `max(3, BENCHMARK_MIN_ORGANIZATIONS)` organizations.
  - v1 benchmarks only identical signatures, not equivalent ones. That keeps the aggregate meaningful.
- **Web.** See decision 5. Offers are stored in a global `web_offers` table with an expiry.

### 5. Web search and page reading

**Searching.** Queries go through `ddgs` with the market's region (`dk-da` for Denmark, from the company's `country_code`). The first query uses the part number or EAN with the market's word for price. If that finds nothing, the product name plus the two most telling attributes is searched. At most `ALTERNATIVES_WEB_QUERIES` (default 2) queries and `ALTERNATIVES_WEB_PAGES` (default 4) pages are used per item. Results on non-shop hosts are skipped by a block list: social, encyclopaedias, company registers, review sites and PDF manuals.

**Reading.** Each page is fetched once through Crawl4AI with the robots.txt check, a timeout and markdown output. The page text is cut to `ALTERNATIVES_PAGE_CHARS`, and the LLM reads its offers into `PageOffers`: seller, product name, identifiers, attributes, price, currency, VAT included or not, pack quantity and unit, and stated shipping. Prices are converted without VAT using a static table of standard rates by seller country (DK 25, SE 25, NO 25, DE 19, NL 21, FI 25.5, GB 20, and so on). The seller's country is taken from the page's host TLD or the market. An offer whose VAT treatment or currency can't be told is dropped.

**Caching and politeness.**
- Pages and their offers are cached for `ALTERNATIVES_OFFER_TTL_DAYS` in `web_pages` (url, fetched_at, status) and `web_offers`. Both are shared across organizations, since they're public.
- A failed page is not retried within the TTL.
- A per-host minimum interval (`ALTERNATIVES_HOST_INTERVAL_S`, default 5) is kept by the worker in memory. There is one worker process today, as `design.md` of the agreement work assumes.

*Alternatives considered.*
- Paid search or shopping APIs (Google Shopping, PriceRunner) give cleaner prices, but need keys and contracts; DDG is already in use. The search is behind one module, so a paid provider can replace it later.
- Plain HTTP fetching without robots.txt was rejected for politeness.

### 6. Runs, scan and on-request search

`pipeline_runs` gets a nullable `params` JSON column. `find_alternatives` carries `{item_id}`, and a request reuses a queued run with the same params.

The worker's tick queues one `scan_alternatives` system run per active company when `ALTERNATIVES_SCAN_ENABLED` is set and the company's last scan is older than `ALTERNATIVES_SCAN_INTERVAL_HOURS`.

A scan does four things:
1. refreshes `company_items`;
2. extracts the missing specifications for the due items;
3. updates the specification index;
4. searches up to `ALTERNATIVES_SCAN_ITEMS` due items, largest spend first.

A search replaces the item's open alternatives per source searched. Each alternative has a stable `ref_key` (the other item's key, the benchmark's product or signature, or the offer URL plus product), so reviewed alternatives are kept and dismissed refs are skipped.

Scans run below agreement analysis and document reads in the queue order, since they are the most expensive and the least urgent.

### 7. Agreement conflicts

For an item, the in-scope rulings of confirmed terms of active agreements are looked up by `item_key`, using `agreement_scope_judgements` as compliance does. Two cases are noted on the alternative:
- **Preferred supplier:** the alternative's supplier is not the agreement's. For history, the vendor is compared; for the web, the offer's host is compared with the vendor's website.
- **Volume commitment:** the term is behind, per `commitment_progress`.

The note is text plus the agreement id, so the UI links to the agreement.

### 8. API and UI

**web-api:**
- `GET /alternatives` lists items with their best open alternative, with filters and paging, and the total.
- `GET /items/{id}` returns an item with its specification and alternatives.
- `PATCH /items/{id}/specification` is for managers and audited.
- `POST /items/{id}/find-alternatives` is for managers.
- `PATCH /alternatives/{id}` reviews an alternative and is audited.
- `GET /invoice-lines/{id}` gets the line's `item_id`.
- The organization endpoint gets `price_benchmark_enabled` (org admin).

**web:**
- `/alternatives` (list) and `/alternatives/$itemId` (item), each a presentational panel driven by its route.
- An "Alternatives" sidebar entry.
- The action in the spend-line drawer.
- A toggle in the organization settings.

### 9. Removing the stubs

The `procurement_agent` and `redundancy` packages and their `_call_stub` calls in `sync/runner.py` are removed. The sync's steps are renumbered. The `recommendations` table, the `Company.recommendations` relationship and its deletion in `company_deletion.py` are dropped in the migration. **BREAKING** only in name: nothing reads them.

## Risks / Trade-offs

- **Specifications read wrong** (a pack size or grade misread). → Confidence is shown; a manager can correct the specification and the correction sticks; low-confidence specifications (< 0.5) get no web search until confirmed.
- **Wrong web prices** (a pack price read as a unit price, or a member-only price). → The pack quantity must be stated, otherwise the offer is dropped. Every web alternative links to its page with the date it was seen, and "price wrong" dismissals are counted per host, so a host with repeated wrong prices can be blocked.
- **DDG blocks or throttles the worker.** → Searches are cached per query for the TTL, there is a host interval, the number of queries per run is low, and the web source sits behind `ALTERNATIVES_WEB_ENABLED` (default off). History and the benchmark work without it.
- **Website terms and scraping.** → robots.txt is honoured, volumes are low and cached, and only publicly listed prices are read. Turning the web source on for production needs a deliberate decision (open question).
- **Benchmark re-identification** (with three organizations, one may guess the others). → At least three others besides the viewer, only the median and lowest quartile, no supplier or buyer. Organizations can opt out.
- **GPU load** from extraction, comparison and page reading. → Everything is batched and cached. The scan is capped per run, off by default, and queued behind interactive work.
- **Quantity missing on many ERP lines.** → Those items have no unit price and say why. History and the benchmark still show identifiers and prices, but no saving.
- **One worker assumed** for the host interval. → Documented. A shared limiter (a table) is needed before running several workers.

## Migration Plan

1. Migration `0023_cheaper_alternatives`:
   - **new tables:** `company_items`, `products`, `spec_comparisons`, `web_pages`, `web_offers`, `item_alternatives`;
   - **new columns:** `pipeline_runs.params` and `organizations.price_benchmark_enabled` (default true);
   - **dropped:** `recommendations`.
2. Deploy web-api and the worker; the flags default to history and benchmark on request only.
3. Run `find_alternatives` on a few items of the test company; then turn on `ALTERNATIVES_SCAN_ENABLED`, and `ALTERNATIVES_WEB_ENABLED` once the web terms question is settled.
4. Rollback: the downgrade drops the new tables and columns. `recommendations` is recreated empty.

## Open Questions

- **Benchmark default:** should taking part be on by default, as proposed, or should organizations opt in? This is a legal and terms-of-service question for Spendyard, not a technical one.
- **Marketplaces:** are Amazon and similar valid sellers for alternatives, or only shops and supplier sites?
- **No country:** for a company without a `country_code`, should the market come from its base currency, or should the web search be skipped (as proposed)?
- **Paid shopping API:** is a paid search or shopping API worth its cost for better coverage of finished goods?
