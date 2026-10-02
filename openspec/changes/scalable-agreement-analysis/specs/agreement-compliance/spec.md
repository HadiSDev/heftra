## MODIFIED Requirements

### Requirement: Lines SHALL be matched to confirmed terms by retrieval and a cached scope judgement

For each confirmed term of an active agreement, analysis SHALL consider the company's **items** (see `spend-item-index`) that have lines invoiced within the agreement's validity; an agreement with no end date is open-ended. An item SHALL be a candidate for a term when either:
- its spend category is one of the term's scope categories, or below one (or, for a term without scope categories, one of the categories suggested for its item or scope; the suggestion SHALL be saved on the term, where a person sees it and can change it). This is selected in SQL.
- it is among the items most similar to the term's scope or item, above a threshold. This is searched in the item index.

Candidates per term SHALL be capped at `AGREEMENT_CANDIDATES_MAX` items, the most spend first. A capped term SHALL be counted in the run's summary.

Each candidate item SHALL be judged by the LLM against the term, once, and the answer SHALL apply to every line of the item. The judge answers:
- whether the item is in scope, with a confidence and a one-sentence reason;
- for an agreed-price term, also whether it is the priced item, and whether its unit is comparable to the agreed unit.

Up to `AGREEMENT_JUDGE_BATCH` items of one term MAY be asked in one prompt, and up to `AGREEMENT_JUDGE_CONCURRENCY` prompts SHALL run at once. A batched answer that can't be parsed SHALL be asked again item by item before an item is left unjudged.

Answers SHALL be cached, keyed by:
- the term's judged fields;
- the buyer's description;
- the judge's version;
- the item.

A later run SHALL only judge items it hasn't judged. Editing a term's scope or item SHALL make its items be judged again. An item left unjudged SHALL be counted, and asked again on the next run.

#### Scenario: A laptop is in scope for IT equipment

- **WHEN** a confirmed preferred-supplier term covers "IT equipment" and an item reads "Dell Latitude 5450 laptop"
- **THEN** the item is judged in scope with a reason, and every line of it is analysed as in scope

#### Scenario: A lookalike is not

- **WHEN** an item reads "Laptop sleeve 14 inch" and the term is an agreed price for "Lenovo ThinkPad T14 Gen 5"
- **THEN** the item is judged not the priced item

#### Scenario: Thousands of identical lines are one question

- **WHEN** 12,000 lines are the same keyboard from the same supplier
- **THEN** the judge is asked about the keyboard once for each term that considers it

#### Scenario: Only new items are judged

- **WHEN** analysis runs again after a sync added lines of one new item and more lines of known items
- **THEN** only the new item is sent to the LLM, and the known items are counted as cached

### Requirement: Findings SHALL be calculated from in-scope lines, with amounts and reasons

A line SHALL count as from the agreement's supplier when its invoice's vendor is that vendor, or has the same international VAT number. For each in-scope line, analysis SHALL record:

- **Preferred supplier:**
  - a line from the supplier adds to the term's spend totals, with no finding;
  - a line from any other supplier is an **`off_contract`** rule break. Its amount is the line's net spend in base currency, and its reason names the term, its conditions and the supplier used.
- **Agreed price, for the priced item with a comparable unit.** The price paid per unit, the line's net amount over its quantity (its unit price when it has no quantity), is converted to the agreement's currency at the invoice date.
  - From the supplier: above the agreed price by more than the tolerance is an **`overcharge`** rule break, of (actual − agreed) × quantity in base currency; otherwise it is `compliant`.
  - From another supplier: a `potential_saving` of (actual − agreed) × quantity when positive. It is also `off_contract` when a preferred-supplier term of the same agreement covers the line.
  - An incomparable unit gives `price_unverifiable`.
- **Discount:**
  - From the supplier: a discount of at least the agreed rate, less the tolerance, shown on the line or as a discount line on the same invoice, is `compliant`. Otherwise it is **`missed_discount`**, of the rate × the line's net spend.
  - From another supplier: a `potential_saving` of the rate × its net spend.
- **Volume commitment:** in-scope spend with the supplier adds to the term's spend totals, with no finding per line.

Every in-scope line SHALL add its net spend to the term's totals for its month, split by whether it is from the supplier.

Each finding SHALL record:
- its severity: `rule_break` for `off_contract` and `overcharge`; `warning` for `missed_discount` and `price_unverifiable`; `info` otherwise;
- its amount, its expected and actual values, its quantity, its reason, and the judge's confidence.

In-scope lines SHALL be read in pages, and their findings and totals written and committed per page.

#### Scenario: A laptop bought from a webshop

- **WHEN** an active agreement with Atea says IT equipment is bought from Atea, and a line "Dell Latitude 5450" for DKK 9,200 is invoiced by Proshop within the validity
- **THEN** there is an `off_contract` rule break of DKK 9,200 whose reason names the term, the "when in stock" condition, and Proshop

#### Scenario: A laptop bought from the supplier

- **WHEN** the same agreement and a line "Lenovo ThinkPad T14" for DKK 8,000 invoiced by Atea
- **THEN** there is no finding for it, and the term's totals for that month gain DKK 8,000 with the supplier

#### Scenario: An overcharged laptop

- **WHEN** the agreed price for a ThinkPad T14 Gen 5 is DKK 8,000 and Atea invoices 3 at DKK 8,400
- **THEN** there is an `overcharge` rule break of DKK 1,200, with expected 8,000 and actual 8,400

#### Scenario: A box against a unit

- **WHEN** the agreed price is per unit and the line is for a box of 10
- **THEN** the finding is `price_unverifiable` and no overcharge is claimed

#### Scenario: A missing discount

- **WHEN** a 10% accessories discount applies and Atea invoices a DKK 1,000 docking station with no discount on the line or the invoice
- **THEN** there is a `missed_discount` warning of DKK 100

### Requirement: Volume commitments SHALL report their progress

For each confirmed volume commitment, the report SHALL give:
- the in-scope spend with the supplier in the current commitment period, summed from the term's monthly totals;
- the committed amount, and the target pro rata to today;
- a linear forecast to the end of the period;
- the rebate tier reached and the next one, when the term has tiers.

#### Scenario: Behind on a commitment

- **WHEN** a DKK 500,000 yearly commitment is at DKK 150,000 halfway through the year
- **THEN** progress shows DKK 150,000 against a pro-rata target of DKK 250,000, with a forecast of DKK 300,000

### Requirement: Findings SHALL be stored, refreshed by analysis runs, and keep their review

Findings SHALL be stored per term, line and kind, and spend totals per term, month and whether from the supplier.

Each agreement SHALL keep a watermark: when its last complete run started. An **incremental** run SHALL:
- recalculate the lines added or changed since the watermark: a line or its invoice has a later `changed_at`, which moves when its item, amounts or category, or its invoice's supplier, date or currency change;
- recalculate every line of a term confirmed or edited since the watermark;
- delete the findings and totals of terms that are no longer confirmed;
- for those lines, update the findings it produces again, add new ones, and delete the ones it no longer produces;
- adjust the totals by what it removed and added.

A **full** run SHALL recalculate every line of every confirmed term. A full run SHALL happen:
- for an agreement's first run;
- when its validity, supplier or currency changed;
- on request.

The watermark SHALL move only when the run completes. A run that stops part-way SHALL leave its committed pages in place, and the next run SHALL redo the agreement from the old watermark.

An item the judge could not answer for (the model timed out or replied with something unreadable) SHALL keep the findings it had, and the watermark SHALL NOT move, so the next run asks about it again. The report SHALL say how many items the last completed check could not judge.

A finding's review SHALL survive re-analysis while the same term, line and kind is still produced. Its review status is `open`, `exception` or `not_in_scope`, with a note, who reviewed it and when.

A manager SHALL be able to review a finding through `PATCH /api/v1/agreement-findings/{id}`: mark it as an exception or as not in scope with a note, or reopen it. That SHALL be audited. Once any finding of a line against a term is marked `not_in_scope`, later runs SHALL NOT raise that line against that term, and SHALL keep that finding as the record of the decision.

#### Scenario: An accepted exception stays accepted

- **WHEN** a manager marks an off-contract finding as an exception ("Atea out of stock, urgent replacement") and analysis runs again
- **THEN** the finding is still an exception with that note

#### Scenario: Not in scope is learnt

- **WHEN** a manager marks a finding as not in scope
- **THEN** later runs don't raise that line against that term

#### Scenario: A sync only checks what it brought

- **WHEN** a sync adds 5,000 lines to a company with 2,000,000 analysed lines and an active agreement
- **THEN** the incremental run reads and writes only those 5,000 lines' findings and totals

#### Scenario: A recategorized line is checked again

- **WHEN** a line's category is changed after analysis
- **THEN** the next incremental run recalculates that line

#### Scenario: A run that stopped is redone

- **WHEN** the worker stops half-way through an agreement's run
- **THEN** its watermark is unchanged and the next run covers the same lines again, without duplicating findings or totals

#### Scenario: The model does not answer for an item

- **WHEN** the model times out on an item that had an off-contract finding
- **THEN** the finding stays, the report says one item could not be judged, and the next run asks about that item again

### Requirement: Analysis SHALL run when terms or spend change, and on request

A company's `analyse_agreements` run SHALL be requested:
- when a term of one of its agreements is confirmed, or a confirmed term is edited or rejected;
- by the worker, as a system run, after the company's `sync`, `read_documents` or `categorize` run succeeds, when it has an active agreement;
- by a manager, through `POST /api/v1/companies/{id}/agreements/analyse`. With `full=true`, it is a full run.

A request SHALL return the queued run of that kind rather than add another; a request for a full run SHALL make the queued run a full one. While one is running, a request SHALL queue another, so that a change made during a run is analysed. The run's summary SHALL count:
- the terms analysed;
- whether each agreement's run was full or incremental;
- the candidate items, and the judged, cached and unjudged ones;
- the capped terms;
- the lines read and the pages written;
- the findings by kind;
- whether similarity search was available.

#### Scenario: New spend is checked

- **WHEN** a sync brings in new lines for a company with an active agreement
- **THEN** an `analyse_agreements` run is queued for it

#### Scenario: A manager asks for everything again

- **WHEN** a manager requests analysis with `full=true`
- **THEN** the queued run recalculates every line of every confirmed term

### Requirement: The agreement report and the dashboard SHALL summarise findings

`GET /api/v1/agreements/{id}/report` SHALL return:
- the totals by kind and severity of the open findings: count and amount;
- the in-scope spend and the share of it with the supplier, from the spend totals of the agreement's broadest confirmed term (the one with the most spend in scope);
- commitment progress;
- the findings, filterable by kind and review status, rule breaks first. Each finding SHALL have its line's date, supplier, item and voucher.

`GET /api/v1/reports/agreement-compliance?from=&to=&company_id=` SHALL return, for the period and the caller's scope:
- the count and amount of open rule breaks;
- the off-contract spend;
- the overcharges;
- the five suppliers with the most off-contract spend.

Both SHALL answer from indexed queries over findings and totals, without reading invoice lines.

#### Scenario: The report leads with rule breaks

- **WHEN** an agreement has two rule breaks, a warning and several lines bought from the supplier
- **THEN** the report's findings list the two rule breaks first, its totals give their count and amount, and its spend in scope includes the supplier's lines
