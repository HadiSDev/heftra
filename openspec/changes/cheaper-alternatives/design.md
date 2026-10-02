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
- Exact and similar alternatives from the organization's own purchases, other customers' anonymous prices and marketplace connectors: the same kind of product, never worse on a key attribute, and never a lower tier of processor, graphics or grade.
- A yearly saving per alternative, items ranked by it, and the scan and on-request search.
- Bounded cost: LLM calls, searches and page reads per run are capped; everything that can be reused is cached.
- Prices shared between organizations only as anonymous aggregates of three or more.

**Non-Goals:**
- Ordering, requests for quotes or negotiating with suppliers.
- Shipping costs, minimum order quantities, lead times or stock in the price. They are shown when a page states them, but not included.
- Commodity price indices for materials (steel, copper, timber) and price forecasting. The existing `price-indices` capability can feed them later.
- Supplier catalogues or price lists uploaded by a person. That is a later source, and fits the connector interface.
- Customer-connected marketplaces (Amazon Business, Unite) and punchout. They need the customer's account and come in a later change.
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

### 3. Matching: exact by identifiers, similar by product type, attributes and tiers

The candidate pipeline for an item, cheapest checks first:
1. **Exact.** Same product, or the same GTIN, part number or brand and model, decided in code after normalising (upper case, no spaces or hyphens).
2. **Same class, pricing unit and product type,** or the candidate is dropped. Product types are compared by the LLM, once per pair of types, and cached ("business laptop" against "2-in-1 tablet" is a different kind).
3. **Numeric attributes**, compared in code, after converting units with a small table (mm, cm, m; g, kg; GB, TB; W; V; in). The attribute's direction decides better or worse; "must be equal" allows `ALTERNATIVES_EQUAL_TOLERANCE_PERCENT`. A missing attribute rejects the candidate.
4. **Tiered attributes**, compared in code when both parts are in a known family, by a `tiers.py` table:
   - the table holds each family's ordered tiers (Intel Core i3/i5/i7/i9, Core Ultra 5/7/9, Ryzen 3/5/7/9, Apple M/Pro/Max/Ultra, steel grades S235 < S275 < S355 < S460 within EN 10025);
   - each part is parsed into family, tier and generation by pattern (i7-1355U is Core, tier 7, generation 13; Core Ultra 7 155U is Core Ultra, tier 7, series 1);
   - a lower tier is worse, whatever the generation; the same or a higher tier with an older generation is worse;
   - across families, or for a part the table can't parse, the LLM decides conservatively, with a reason, and "uncertain" counts as worse.

   This is what keeps an i3 or i5 from ever replacing an i7.
5. **Other attributes**, compared by the LLM in one batched prompt per item. For each pair it returns same, better or worse, with a reason. Any worse rejects the candidate.
6. **Cached comparisons.** LLM comparisons are stored in `spec_comparisons`, keyed by the two specification hashes and the version, so the same pair is never asked twice, for any company.

*Alternatives considered.*
- LLM-only matching sometimes waves through less memory, a thinner ply or a lower processor tier, and the user asked that alternatives be similar, never worse.
- A fully deterministic match can't tell that S355J2 is at least S235JR, or compare an Intel part with an AMD one.
- Benchmark scores for processors (PassMark and the like) were considered for tiers. They need a licensed data source and still don't stop a "faster" i5 from replacing an i7, which the user ruled out.

### 4. Sources

- **History.** Two queries over `company_items` of the same organization in the last 12 months: items with the same product, and the top `ALTERNATIVES_SIMILAR` hits from the specification index for the organization, class and pricing unit. Both are cheaper by the threshold. The alternative names the supplier, the company and the last purchase date.
- **Benchmark.** Per-organization prices for the item's product, or for items with the same **specification signature** (a hash of class, pricing unit and normalised key attributes), from organizations taking part other than the viewer's.
  - Each organization contributes its spend-weighted unit price in EUR, converted to the viewer's base currency.
  - Median and lowest quartile are computed in Python over at most a few hundred per-organization prices, never from line data.
  - The benchmark is shown only from at least `max(3, BENCHMARK_MIN_ORGANIZATIONS)` organizations.
  - v1 benchmarks only identical signatures, not equivalent ones. That keeps the aggregate meaningful.
- **Marketplaces.** See decision 5.

### 5. Marketplace connectors

Marketplaces sit behind one interface:
- `OfferSource.search(item_spec, market) -> list[Offer]`, with a `name`;
- an `enabled()` check (flag and credentials);
- a per-provider rate limiter.

An `Offer` holds seller, title, identifiers, attributes, price (with quantity breaks), currency, VAT included, pack quantity and unit, stock, shipping when stated, URL and seen-at. Offers are normalised to the item's specification by the same extraction prompt, run on the offer's title and attributes, so matching treats every source alike.

The v1 connectors are all free:
- **Shop search** (`shops.yaml`). A curated list of shops per market, each with a search URL template and the hosts its product pages live on. Examples for Denmark: Proshop, Komplett, Computersalg and Dustin for IT; Lyreco and Office Depot for office supplies; Sanistål and Lemvigh-Müller for materials, where list prices are public. The list is data, so shops can be added without code.
  - The search results page is crawled for product links.
  - Then up to `ALTERNATIVES_PAGES_PER_ITEM` product pages are crawled.
  - The queries are the part number or EAN first, then the product name with its two most telling attributes.

  Searching one shop directly finds that shop's listing far more reliably than a general web search does.
- **Open web.** Web search through a `SearchProvider`. The default is a self-hosted **SearXNG**, a free metasearch engine, run as a `searxng` service in `docker-compose.yml` (port 8888, `SEARXNG_URL=http://localhost:8888`). Its settings enable the JSON output format and turn off the limiter, since only the worker calls it. Queries go to `/search?format=json` with the market's language (`language=da-DK`) and a few general engines (Google, Bing, Brave, DuckDuckGo); SearXNG spreads the load across them, so no single engine throttles the worker. When `SEARXNG_URL` is unset or SearXNG can't be reached, DuckDuckGo (`ddgs`, keyless) is the fallback, and the run's summary says so. Hosts on the block list (social, encyclopaedias, company registers, reviews, manuals) are skipped. The remaining product pages are crawled the same way.
- **Distributors.** Farnell (element14), Mouser and Digi-Key, each a small client of its public product-search API with a free developer key: element14's `catalog/products` with the market's store (`dk.farnell.com`), Mouser's v1 keyword search, and Digi-Key's v4 keyword search with OAuth client credentials and the market's site and currency. Each is enabled only when its key is set. They search by keyword, which matches manufacturer part numbers too. RS is left out of v1: its API is given through a partner programme without a public specification to build against. Price breaks are read at the item's typical order quantity: the average quantity per line.

**Reading a product page.**
- **Fetching.** Pages are fetched with Crawl4AI, as supplier enrichment does: the robots.txt check, a timeout, and a per-host minimum interval (`ALTERNATIVES_HOST_INTERVAL_S`, default 5) kept in the worker.
- **Structured data first.** Offers are read from the page's schema.org `Product` / `Offer` data first, in JSON-LD or microdata: name, GTIN, SKU, MPN, brand, price, currency, availability, and `priceSpecification` with `valueAddedTaxIncluded` when given. Most webshops embed this data for search engines. It's exact, and costs no LLM call.
- **The model fills gaps.** It reads the page's cleaned markdown, cut to `ALTERNATIVES_PAGE_CHARS`, only for what the structured data leaves out. That's usually the key attributes, and the VAT treatment when the data doesn't state it. On a page without structured data, the model reads the whole offer.
- **Same specification.** The result is normalised to a specification by the same extraction as items, so matching treats every source alike.

**VAT.** A price stated with VAT is converted without it using a static table of standard rates by seller country (DK 25, SE 25, NO 25, DE 19, NL 21, FI 25.5, GB 20, and so on). Distributor APIs state prices without VAT. An offer whose VAT treatment, currency or pack quantity can't be told is dropped.

**Caching.** Each connector's answers are cached in `marketplace_queries` (connector, query, market, fetched_at), with their offers in `marketplace_offers`, for `ALTERNATIVES_OFFER_TTL_DAYS`. Both are shared across organizations, since the data is public. A failing connector is counted in the run's summary and skipped for the rest of the run.

**Credentials.** The distributor connectors use Spendyard's own free developer keys, from the environment (`FARNELL_API_KEY`, `MOUSER_API_KEY`, `DIGIKEY_CLIENT_ID`/`DIGIKEY_CLIENT_SECRET`), not the customer's. A paid shopping-search API (SerpApi or DataForSEO) fits the same `SearchProvider` interface, and can be added later if the free search proves too thin. Customer-connected marketplaces (Amazon Business, Unite) need the customer's account through OAuth and are left for a later change. The interface allows a per-organization credential then.

*Alternatives considered.*
- A paid shopping-search API (SerpApi, DataForSEO) gives cleaner results across many shops, but costs per query. v1 starts free, and the provider interface keeps a paid one open.
- Reading prices from page text with the model alone misreads pack and member prices; structured data comes first.
- Scraping marketplaces directly breaks their terms and fails whenever a page changes.
- Affiliate APIs (Amazon PA-API, price comparison sites) depend on generating sales and restrict how their data may be used.

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
- `GET /invoice-lines/{id}/item` returns a spend line's item, and `POST /invoice-lines/{id}/find-alternatives` keys the line when needed, stores its item and queues its search. The item key function and the specification, unit and pricing models live in web-api (`web_api.items`, `web_api.specs`) so both the API and the worker use them; the search run refreshes the item's figures first.
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
- **Wrong marketplace prices** (a pack price read as a unit price, or a member-only price). → The pack quantity must be stated, otherwise the offer is dropped. Every marketplace alternative links to its offer with the date it was seen, and "price wrong" dismissals are counted per seller, so a seller with repeated wrong prices can be blocked.
- **Pages without the attributes.** → Equivalence needs them, so the model reads the page text for them; without the attributes the candidate is only kept when it is an exact match.
- **Free search is thin or throttled** (DuckDuckGo limits automated queries). → The shop search doesn't depend on it. SearXNG spreads queries over several engines, and DuckDuckGo is only the fallback. Queries are cached for 14 days, and few are made per item.
- **Shops change their search pages or block crawlers.** → The shop list is data; a shop whose search returns nothing for a week is reported in the run summaries. robots.txt is honoured, and a blocked shop is skipped.
- **Website terms.** → Only public list prices are read, robots.txt is honoured, volumes are low and cached, and shops are listed deliberately.
- **Tier tables go out of date** (new processor generations, new families). → An unknown part falls back to the conservative LLM decision, which counts "uncertain" as worse, so a new part is missed rather than wrongly accepted; the table is data, extended in one place.
- **Distributor API quotas** (daily limits on free keys). → Answers are cached for 14 days and shared, queries per item are capped, the scan is capped per run, and each connector has its own flag.
- **Benchmark re-identification** (with three organizations, one may guess the others). → At least three others besides the viewer, only the median and lowest quartile, no supplier or buyer. Organizations can opt out.
- **GPU load** from extraction, comparison and page reading. → Everything is batched and cached. The scan is capped per run, off by default, and queued behind interactive work.
- **Quantity missing on many ERP lines.** → Those items have no unit price and say why. History and the benchmark still show identifiers and prices, but no saving.
- **One worker assumed** for the host interval. → Documented. A shared limiter (a table) is needed before running several workers.

## Migration Plan

1. Migration `0023_cheaper_alternatives`:
   - **new tables:** `company_items`, `products`, `spec_comparisons`, `marketplace_queries`, `marketplace_offers`, `item_alternatives`;
   - **new columns:** `pipeline_runs.params` and `organizations.price_benchmark_enabled` (default true);
   - **dropped:** `recommendations`.
2. Deploy web-api and the worker; the flags default to history and benchmark on request only.
3. Start the `searxng` service and set `SEARXNG_URL`; optionally create free developer keys for the distributors. Run `find_alternatives` on a few items of the test company, then turn on `ALTERNATIVES_SCAN_ENABLED`.
4. Rollback: the downgrade drops the new tables and columns. `recommendations` is recreated empty.

## Open Questions

- **Benchmark default:** should taking part be on by default, as proposed, or should organizations opt in? This is a legal and terms-of-service question for Spendyard, not a technical one.
- **No country:** for a company without a `country_code`, should the market come from its base currency, or should the web search be skipped (as proposed)?
- **The first shop list:** which Danish shops matter most to the first customers, per kind of spend (IT, office, cleaning, food, materials)?
- **Tier table scope:** beyond processors, graphics and steel grades, which tiered families matter most to customers (paper quality classes, screw strength classes, cable categories)?
