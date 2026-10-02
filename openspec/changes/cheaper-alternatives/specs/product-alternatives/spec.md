## ADDED Requirements

### Requirement: Items of the same product SHALL be recognised across suppliers and companies

Items SHALL be linked to a **product** when they are the same thing: the same manufacturer part number or EAN/GTIN, or the same brand and model with no key attribute that differs. Items from different suppliers, different companies and different organizations SHALL share a product when they match. An item with no identifier SHALL have no product and SHALL be matched by its specification alone.

#### Scenario: One keyboard, two suppliers

- **WHEN** one company buys "Magic Keyboard Touch Id Num Key (MXK73DK/A)" from CS-Online and another buys "Apple Magic Keyboard med Touch ID og numerisk tastatur MXK73DK/A" from Proshop
- **THEN** both items are linked to the product with part number MXK73DK/A

### Requirement: An alternative SHALL be exact or a similar product, and never worse

A candidate SHALL be an alternative to an item only when its class and pricing unit are the item's, and it is either:
- **exact**: the item's product, or the same part number, EAN or brand and model;
- **equivalent**: a similar product, judged by all of the following:
  - it is the **same kind of product** for the same use: a business laptop for a business laptop (not a gaming laptop or a tablet), a round bar for a round bar, the same cable category and construction;
  - every **numeric** key attribute is met or bettered, compared in the attribute's unit by its direction (more is better, less is better). An attribute that must be equal, such as a dimension a part is cut to, a thread or a screen size, SHALL be equal within `ALTERNATIVES_EQUAL_TOLERANCE_PERCENT` (default 2);
  - every **tiered** attribute, such as a processor, a graphics card or a steel or quality grade, SHALL be the same tier or higher **and** the same generation or newer. A lower tier SHALL be worse whatever its generation: an Intel Core i3 or i5 is never an alternative to a Core i7, and a newer i5 is not either. Tiers SHALL be ordered within a family (Intel Core i3 < i5 < i7 < i9, Core Ultra 5 < 7 < 9, AMD Ryzen 3 < 5 < 7 < 9, Apple M < M Pro < M Max < M Ultra). Across families the LLM SHALL decide, conservatively: only a part of the same class of performance and age counts as the same tier, and anything uncertain counts as worse;
  - any other attribute (a material, a coating, a jacket, a certification) SHALL be judged by the LLM as the same, better for the buyer's purpose, or worse, with a one-sentence reason.

A candidate that is worse on any key attribute, does not state one, or is a different kind of product SHALL NOT be an alternative. Each alternative SHALL carry the item's and the candidate's attributes side by side, each marked as same, better or worse.

#### Scenario: A better steel grade is equivalent

- **WHEN** the item is a 20 mm round bar in S235JR and a candidate is the same bar in S355J2
- **THEN** the candidate is equivalent, with the grade marked better

#### Scenario: A lower processor tier is never an alternative

- **WHEN** the item is a laptop with an Intel Core i7-1355U and cheaper candidates have an i3-1315U and an i5-1435U
- **THEN** neither is an alternative

#### Scenario: An older generation of the same tier is not an alternative

- **WHEN** the item has a 13th-generation Core i7 and a candidate has an 11th-generation Core i7
- **THEN** the candidate is not an alternative

#### Scenario: Another family of the same tier and age

- **WHEN** the item has an Intel Core i7-1355U and a candidate an AMD Ryzen 7 7730U, otherwise the same or better
- **THEN** the candidate is equivalent only if the LLM judges the processors the same tier and age, and the reason is shown beside them

#### Scenario: Less memory is not an alternative

- **WHEN** the item is a laptop with 16 GB memory and a cheaper candidate has 8 GB
- **THEN** the candidate is not an alternative

#### Scenario: A different kind of product

- **WHEN** the item is a 14" business laptop and a cheaper candidate with the same processor and memory is a tablet with a keyboard cover
- **THEN** the candidate is not an alternative

#### Scenario: A missing attribute is not assumed

- **WHEN** a cheaper toilet roll candidate doesn't say how many sheets or metres a roll has
- **THEN** it is not an alternative

### Requirement: Prices SHALL be compared per pricing unit, in base currency, without VAT

A candidate's price SHALL be converted to its price per pricing unit (its pack size divided out), to the company's base currency at the rate of the day it was seen, and to a price without VAT: a price stated with VAT SHALL have the standard VAT rate of the seller's country removed. A price whose currency, pack size or VAT treatment can't be told SHALL NOT be used.

A candidate SHALL be an alternative only when its unit price is below the item's by at least `ALTERNATIVES_MIN_SAVING_PERCENT` (default 3). Shipping, minimum order quantities and delivery times SHALL NOT be included in the price; an alternative SHALL show what the seller states of them when it is known.

#### Scenario: A webshop price with VAT

- **WHEN** a Danish webshop sells a pack of 8 rolls for DKK 100 including VAT and the item costs DKK 11 per roll
- **THEN** the candidate costs DKK 10 per roll without VAT, and is an alternative saving about 9 %

#### Scenario: Too small a saving

- **WHEN** a candidate is 1 % cheaper than the item
- **THEN** it is not an alternative

### Requirement: Each alternative SHALL estimate a yearly saving

An alternative's **yearly saving** SHALL be the item's unit price less the alternative's, times the item's yearly quantity, in base currency. An item's best alternative is its largest saving. Items SHALL be ranked by their best saving.

#### Scenario: Saving on cable

- **WHEN** the item costs DKK 3.00 per metre with 1,220 m bought last year and an alternative costs DKK 2.40 per metre
- **THEN** the alternative's yearly saving is DKK 732

### Requirement: Alternatives SHALL come from the organization's own purchases

An item's alternatives SHALL include the exact and equivalent items bought in the last 12 months by any company of the same organization, from any supplier, at a lower unit price. Such an alternative SHALL name the supplier, the company and when it was last bought.

#### Scenario: The same keyboard cheaper at another supplier

- **WHEN** a company paid DKK 1,136 per keyboard from CS-Online and DKK 999 for the same part number from Proshop last month
- **THEN** the CS-Online item has an exact alternative from Proshop at DKK 999, bought last month

### Requirement: Alternatives SHALL come from other customers' prices

An item's alternatives SHALL include the price benchmark of its product or of equivalent items (see `price-benchmark`) when it is lower. Such an alternative SHALL say how many organizations it comes from and SHALL name no buyer and no supplier.

#### Scenario: Others pay less for steel

- **WHEN** five other organizations paid a median of DKK 9.10 per kg for 20 mm S235JR round bar and the company pays DKK 10.40
- **THEN** the item has an alternative "other customers pay a median of DKK 9.10 per kg (5 organizations)"

### Requirement: Alternatives SHALL come from marketplace connectors

An item's alternatives SHALL include **offers** from marketplace connectors. Every connector SHALL take an item's identifiers and specification and the company's market, and return offers: seller, product, identifiers, attributes, price, currency, whether VAT is included, pack size, stock when stated, and a link. A connector SHALL be used only when it is enabled and its credentials are configured, and SHALL be rate-limited to its provider's limits.

The v1 connectors SHALL need no paid service:
- **shop search**: a configured list of shops per market, each with its site-search URL. The shop's search results and product pages SHALL be crawled, searched by identifiers first and by product name with key attributes otherwise;
- **open web**: a web search through a self-hosted SearXNG at `SEARXNG_URL` (DuckDuckGo only when SearXNG isn't configured or can't be reached), in the market's language, and crawling the product pages it finds;
- **distributors**: the product-search APIs of RS, Farnell, Mouser and Digi-Key, each used only when its free developer key is configured, searched by manufacturer part number first and by keyword otherwise. Quantity price breaks SHALL be read at the item's typical order quantity.

A crawled page SHALL be read from its structured product data first (schema.org `Product` and `Offer` in JSON-LD or microdata: name, GTIN, SKU, MPN, brand, price, currency, availability). The LLM SHALL read the page text only when the page has no such data, or to get the attributes the data leaves out. Crawling SHALL honour robots.txt, keep a minimum interval per host, and read at most `ALTERNATIVES_PAGES_PER_ITEM` pages per item.

An offer SHALL be kept for `ALTERNATIVES_OFFER_TTL_DAYS` (default 14) and reused by every search that asks the same connector the same question in that time, for any organization, since it is public. A marketplace alternative SHALL name its connector and seller, link to the offer and say when it was seen.

A connector that fails SHALL be logged and counted in the run's summary, and the other sources SHALL still be searched.

#### Scenario: A cheaper laptop in a Danish shop

- **WHEN** a company pays DKK 9,200 for ThinkPad T14 Gen 5 21ML003XMX and the shop search finds a Danish shop listing that part number for DKK 10,500 including VAT
- **THEN** the item has an exact alternative at DKK 8,400 without VAT, naming the shop, with the link and the date it was seen

#### Scenario: A cable from a distributor at the order quantity

- **WHEN** a company buys Cat6 cable in 305 m boxes, 4 boxes at a time, and a distributor offers the same part at a lower price from 3 boxes
- **THEN** the alternative uses the price for 4 boxes, per metre

#### Scenario: An offer is reused

- **WHEN** two companies' searches ask the same shop for the same part number within 14 days
- **THEN** the shop is crawled once

#### Scenario: A connector is down

- **WHEN** the distributor API fails during a search
- **THEN** the run records the failure, and history, the benchmark and the shop search still give their alternatives

#### Scenario: A product page with structured data

- **WHEN** a crawled product page carries a schema.org Product with GTIN, price DKK 1,249.00 and currency DKK
- **THEN** the offer is read from that data without asking the LLM for the price

### Requirement: Alternatives SHALL be found by a background scan and on request

When `ALTERNATIVES_SCAN_ENABLED` is set, the worker SHALL queue a `scan_alternatives` run for each active company at most once every `ALTERNATIVES_SCAN_INTERVAL_HOURS` (default 24). A scan SHALL search the company's items, largest 12-month spend first, at most `ALTERNATIVES_SCAN_ITEMS` per run, skipping items searched within `ALTERNATIVES_RESCAN_DAYS` (default 30) whose specification hasn't changed.

A person SHALL be able to ask for an item's alternatives at any time. That SHALL queue a `find_alternatives` run for the item; a request while one is queued for the item SHALL reuse it.

A new search of an item SHALL replace its open alternatives from the sources it searched, and SHALL keep reviewed ones.

#### Scenario: The scan covers the largest spend first

- **WHEN** a company has 3,000 items and the scan limit is 50
- **THEN** the 50 items with the most spend in the last 12 months not searched in the last 30 days are searched

#### Scenario: A person asks for one item

- **WHEN** a manager asks for alternatives to a laptop item
- **THEN** a `find_alternatives` run is queued for it, and its alternatives appear when the run succeeds

### Requirement: Alternatives SHALL be reviewable

An alternative's review status SHALL be `open`, `dismissed` or `switched`. A person SHALL be able to dismiss an alternative with a reason (`not_equivalent`, `supplier_not_approved`, `price_wrong` or `other`) and a note, mark it as switched, or reopen it. Reviews SHALL be audited.

A dismissed alternative SHALL NOT be raised again for the same item from the same product or offer. A `not_equivalent` dismissal SHALL also stop that product being proposed as equivalent to the item.

#### Scenario: A dismissed alternative stays dismissed

- **WHEN** a manager dismisses a marketplace offer as `supplier_not_approved` and the item is searched again
- **THEN** that offer is not raised again for the item

### Requirement: An alternative SHALL say when it would break an agreement

When the item falls under a confirmed term of an active agreement (see `agreement-compliance`), an alternative SHALL say what switching would break: buying from another supplier under a preferred-supplier term, or a volume commitment it would put further behind.

#### Scenario: A cheaper laptop elsewhere under a preferred-supplier term

- **WHEN** an item is in scope of a preferred-supplier term for CS-Online and its alternative is a marketplace offer from another shop
- **THEN** the alternative says that buying it there would be off contract under that agreement
