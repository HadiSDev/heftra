# supplier-enrichment Specification

## Purpose
TBD - created by archiving change spend-categorizer-overhaul. Update Purpose after archive.
## Requirements
### Requirement: A supplier's description SHALL be researched once and stored on the global vendor

The platform SHALL be able to fill `Vendor.description` with a short statement of what the supplier sells, derived from web context, and SHALL do so **once per supplier** rather than once per line or once per invoice.

The description is what turns an opaque supplier name into a categorizable fact: "DSB" is three letters, "DSB — Danish State Railways, passenger rail operator" answers the question the taxonomy is asking. `Vendor` is a **global** catalog, so one lookup serves every tenant that has ever bought from that supplier.

#### Scenario: A supplier is researched once

- **WHEN** twenty lines across four invoices name the same supplier
- **THEN** the supplier is researched at most once and all twenty lines read the stored description

#### Scenario: The description reaches the categorizer

- **WHEN** a line's supplier has a stored description
- **THEN** that description is stated in the categorization prompt alongside the supplier's name

#### Scenario: A supplier already described is not re-researched

- **WHEN** enrichment runs against a supplier whose description is already set
- **THEN** no outbound request is made and the stored description is left as it is

### Requirement: Enrichment SHALL be opt-in, and its absence SHALL degrade nothing

Supplier enrichment makes outbound requests to the public web and SHALL therefore be governed by an environment flag, defaulting to **off**, so tests and offline runs make no outbound request. This follows the rule `FX_ENABLED` already sets.

Crawling a supplier's website additionally needs a headless browser, and SHALL be governed by a second environment flag, also defaulting to **off**, that has effect only when enrichment is enabled. With crawling off, enrichment SHALL behave exactly as it does from search snippets alone, and SHALL NOT require the browser or the crawling library to be installed.

With enrichment off, or with a lookup that fails or returns nothing, the supplier's description SHALL remain null and categorization SHALL proceed on the facts that exist. A failure to describe a supplier, including a failure to start the browser, SHALL never fail a line, an invoice, or a sync.

#### Scenario: Off by default

- **WHEN** the enrichment flag is unset
- **THEN** no outbound request is made and every vendor description stays as stored

#### Scenario: Crawling off by default

- **WHEN** the enrichment flag is set and the crawling flag is unset
- **THEN** no browser is started and no supplier website is fetched

#### Scenario: A failed lookup is not a failed line

- **WHEN** a supplier lookup times out
- **THEN** the vendor's description stays null, the line is still categorized, and the sync still completes

#### Scenario: A browser that will not start is not a failed run

- **WHEN** crawling is enabled but the browser cannot be launched
- **THEN** each supplier is described from its search snippets and the enrichment run completes

### Requirement: A researched description SHALL be correctable and SHALL NOT overwrite a human's

An enriched description is a machine's guess about a shared catalog row, and SHALL be treated as one. A description a human has set SHALL NOT be overwritten by a later enrichment run.

Because `Vendor` is global, a description written by enrichment is visible to every tenant, and SHALL therefore state what the supplier sells and nothing tenant-specific.

#### Scenario: A human's description stands

- **WHEN** a person has written a supplier's description and enrichment runs again
- **THEN** the stored description is unchanged

#### Scenario: The buyer's own context comes from the company, not the catalog

- **WHEN** the prompt states who bought the line
- **THEN** it draws that from the buying company, never from the global vendor row

### Requirement: A supplier's description SHALL come from its own website first, and from search snippets otherwise

When site crawling is enabled, enrichment SHALL first try to describe a supplier from its own website (see `supplier-site-crawl`). When no website is found, the site cannot be crawled, or the site yields no description, enrichment SHALL describe the supplier from the web search snippets as it did before this change. A supplier SHALL never be left undescribed by the crawl when the snippets alone would have described it.

#### Scenario: The site is used when there is one

- **WHEN** the supplier's own site is found and yields a description
- **THEN** that description is stored and the snippets are not summarized

#### Scenario: The snippets are used when the site fails

- **WHEN** the supplier's site times out
- **THEN** the description is written from the search snippets, and no website is stored

#### Scenario: Crawling off leaves today's behaviour

- **WHEN** enrichment is enabled and site crawling is not
- **THEN** no site is crawled and the description is written from the search snippets

### Requirement: The supplier's website SHALL be stored on the vendor and SHALL NOT overwrite one already set

`Vendor` SHALL carry a nullable `website`. When a supplier is described from its own site, that site's root SHALL be stored as its website, unless the vendor already has a website, which SHALL be left as it is. The website SHALL be returned wherever a vendor is read through the web API (`VendorRead` and `VendorOverviewRead`).

#### Scenario: The website found is stored

- **WHEN** a supplier with no website is described from `https://danskkaffe.dk/`
- **THEN** its website is `https://danskkaffe.dk/`

#### Scenario: A website already set stands

- **WHEN** a supplier's website is already set and enrichment finds a different one
- **THEN** the stored website is unchanged

#### Scenario: The website is readable through the API

- **WHEN** a client lists suppliers
- **THEN** each supplier carries its `website`, null when none is known

### Requirement: A website the supplier's invoices state SHALL be crawled before any is searched for

A supplier's known website is the one set on it, else the one its invoices' documents print most often among those whose domain names the supplier: by the same name match that picks a site from search results, or, since the supplier printed it, by a domain label that is any word of the name (of at least two letters, legal forms dropped) or begins with the name's first word. A printed website whose domain does not name the supplier, such as a deposit guarantee scheme in a bank's footer, SHALL NOT be a known website. When a supplier has a known website, enrichment SHALL crawl that site directly, without looking for one among the search results, and SHALL keep it as the supplier's website whether or not the site yields the description. Only when no website is known SHALL enrichment search for the supplier's name to find one.

#### Scenario: The invoices print the website

- **WHEN** a supplier's invoices print `https://danskkaffe.dk/` and crawling is enabled
- **THEN** that site is crawled, no search is made to find a site, and the supplier's website is `https://danskkaffe.dk/`

#### Scenario: The printed site does not describe the supplier

- **WHEN** the known website cannot be read
- **THEN** the description is written from the search snippets and the known website is still stored

#### Scenario: A printed address that is not the supplier's

- **WHEN** a bank's invoices print only `https://www.iidraudimas.lt/`, its deposit guarantee scheme
- **THEN** the bank has no known website, and its name is searched for one

#### Scenario: No website known

- **WHEN** neither the supplier nor its invoices state a website
- **THEN** the supplier's name is searched and its site looked for among the results

### Requirement: A described supplier SHALL be able to get a website without being described again

The enrichment CLI SHALL accept `--websites`, which, instead of describing suppliers, stores a website for each described supplier that has none, leaving its description untouched. The website SHALL be its known website when it has one; otherwise one found for its name among the search results, kept only when crawling it confirms it is the supplier's own site. With crawling off, only a known website SHALL be stored.

#### Scenario: A described supplier gets its website

- **WHEN** `--websites` runs with crawling on for a described supplier with no website whose site is found and confirmed
- **THEN** its website is stored and its description is unchanged

#### Scenario: Nothing confirmed

- **WHEN** no site is found for the supplier, or its site says it belongs to someone else
- **THEN** no website is stored

