## Why

Finding the same product, or one that does the same job, for less is the core promise of Spendyard, and today the product only shows where money goes. Companies buy three kinds of things: production materials priced by weight, length or volume (steel, wood, network cable by the metre), parts bought by the piece to build in or to maintain machines (bearings, screws, connectors, cutting inserts, spare parts), and finished goods priced by the piece or pack (toilet paper, laptops, snacks, smartphones). For all of them, a buyer rarely has time to check whether the same specification is sold cheaper elsewhere. We now have what this needs: every distinct item a company buys is known, with its spend and an embedding (`spend-item-index`), Crawl4AI is already used to read supplier sites, and most webshops publish structured product data with prices.

## What Changes

- Each item a company buys gets a **specification**: whether it is a material, a part or a finished good, its identifiers (manufacturer part number, EAN, brand and model), its key attributes (a steel grade and dimensions; a laptop's processor, memory and storage; a toilet roll's ply and sheets), and a **pricing unit** (kg, m, m², m³, l, piece, sheet) with the line's unit converted to it, so a "pack of 8 rolls" and "box of 305 m" compare per roll and per metre.
- **Alternatives** are found from three sources:
  - **the company's own history:** the same or an equivalent product bought cheaper, from another supplier, by another company of the organization, or earlier;
  - **other customers:** what other organizations on Spendyard pay for the same or an equivalent product, shown only as an anonymous aggregate of at least three organizations;
  - **marketplaces:** pluggable connectors, each with its own flag, credentials and rate limit. v1 uses only free means: a configured list of shops searched and crawled with Crawl4AI, a free web search (a self-hosted SearXNG, DuckDuckGo as the fallback) with the found pages crawled, and the Farnell, Mouser and Digi-Key product APIs with free developer keys (RS later, once its partner API is available). Pages are read from their structured product data first, and by the LLM only where that data is missing. A paid shopping-search API and Amazon Business are left for later.
- Every alternative is labelled **exact** (same identifier, or same make and model) or **equivalent**: the same kind of product, with every key attribute met or bettered and tiered parts (processors, graphics, grades) of the same tier or higher and the same generation or newer, so a Core i7 laptop never gets a Core i5 or i3 suggested. The attributes are compared side by side. A product that is worse on any key attribute is never shown.
- Prices are compared **per pricing unit, in the company's base currency, excluding VAT**, and each alternative gets an estimated yearly saving from the last 12 months' quantity.
- Searches run as a **background scan** of each company's largest-spend items, limited per run and repeated after a set number of days, and **on request** from a "Find cheaper alternatives" action on an item.
- A new **Alternatives** page lists items with savings, largest first; an item shows its specification and its alternatives, and a person can dismiss an alternative (with a reason) or mark that they switched.
- The empty `procurement_agent` and `redundancy` stubs the sync calls are removed, and so is the unused `recommendations` table. **BREAKING** in name only: nothing reads them.

## Capabilities

### New Capabilities
- `item-specifications`: a specification and pricing unit per item, extracted once and correctable, and the price per pricing unit of the item's lines.
- `product-alternatives`: finding alternatives from history, other customers and marketplace connectors; exact and equivalent matching with the attributes compared; price normalisation; the estimated saving; the background scan and on-request search; review of alternatives.
- `price-benchmark`: the anonymous pool of what organizations pay per product and specification, its minimum of three organizations, and the organization setting to take part.
- `frontend-alternatives`: the Alternatives page, the item view with its specification and alternatives, and the "Find cheaper alternatives" action.

### Modified Capabilities
- `spend-item-index`: an item's specification and pricing unit are stored with it, and the index can find items of the same product across the company's suppliers.
- `pipeline-runs`: two new run kinds, `find_alternatives` for one item on request and `scan_alternatives` for the background scan, and runs carry parameters.

## Impact

- **ai-api:** new `specs/` (extraction, units), `alternatives/` (sources, matching, saving, scan) and `web_offers/` (search, page reading, offer cache) packages; the worker's tick gets the scan; the `procurement_agent` and `redundancy` stubs and their calls in the sync runner go.
- **web-api:** new tables for stored items with their specifications, products, specification comparisons, marketplace offers, and alternatives with their reviews; a `params` column on pipeline runs and a benchmark setting on organizations; `recommendations` dropped; one migration; routers for alternatives, item specifications and the on-request search; an organization setting for the price benchmark.
- **web:** the Alternatives page and item view, the action on items, and a sidebar entry.
- **External:** crawling shops and found pages with Crawl4AI (robots.txt honoured, per-host interval, cached for 14 days); free web search; optional free developer keys for the Farnell, Mouser and Digi-Key APIs; a SearXNG container; more LLM calls for specification extraction and matching, bounded per run.
- **Data sharing:** prices flow between organizations only as aggregates of at least three organizations, never with the buyer's name; an organization can opt out, and then gets no benchmark either.
