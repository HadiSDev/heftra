## ADDED Requirements

### Requirement: Lines SHALL be matched to confirmed terms by retrieval and a cached scope judgement

For each confirmed term of an active agreement, analysis SHALL consider the company's invoice lines invoiced within the agreement's validity; an agreement with no end date is open-ended. A line SHALL be a candidate for a term when either:
- its spend category is one of the term's scope categories, or below one; or
- its text is among the most similar to the term's scope or item, above a threshold.

Each candidate SHALL be judged by the LLM against the term, which answers:
- whether the line is in scope, with a confidence and a one-sentence reason;
- for an agreed-price term, also whether it is the priced item, and whether its unit is comparable to the agreed unit.

Answers SHALL be cached, keyed by the term's judged fields and the line's question. A later run SHALL only judge pairs it hasn't judged. Editing a term's scope or item SHALL make its pairs be judged again. An answer that can't be parsed SHALL leave the pair unjudged, and it SHALL be counted.

#### Scenario: A laptop is in scope for IT equipment

- **WHEN** a confirmed preferred-supplier term covers "IT equipment" and a line reads "Dell Latitude 5450 laptop"
- **THEN** the line is judged in scope with a reason

#### Scenario: A lookalike is not

- **WHEN** a line reads "Laptop sleeve 14 inch" and the term is an agreed price for "Lenovo ThinkPad T14 Gen 5"
- **THEN** the line is judged not the priced item

#### Scenario: Only new pairs are judged

- **WHEN** analysis runs again after one new line was synced
- **THEN** only the new line's pairs are sent to the LLM, and the rest are counted as cached

### Requirement: Findings SHALL be calculated from in-scope lines, with amounts and reasons

A line SHALL count as from the agreement's supplier when its invoice's vendor is that vendor, or has the same international VAT number. For each in-scope line, analysis SHALL record:

- **Preferred supplier:**
  - a line from the supplier is `compliant`;
  - a line from any other supplier is an **`off_contract`** rule break. Its amount is the line's net spend in base currency, and its reason names the term, its conditions and the supplier used.
- **Agreed price, for the priced item with a comparable unit.** The line's unit price is converted to the agreement's currency at the invoice date.
  - From the supplier: above the agreed price by more than the tolerance is an **`overcharge`** rule break, of (actual − agreed) × quantity in base currency; otherwise it is `compliant`.
  - From another supplier: a `potential_saving` of (actual − agreed) × quantity when positive. It is also `off_contract` when a preferred-supplier term of the same agreement covers the line.
  - An incomparable unit gives `price_unverifiable`.
- **Discount:**
  - From the supplier: a discount of at least the agreed rate, less the tolerance, shown on the line or as a discount line on the same invoice, is `compliant`. Otherwise it is **`missed_discount`**, of the rate × the line's net spend.
  - From another supplier: a `potential_saving` of the rate × its net spend.
- **Volume commitment:** in-scope spend with the supplier counts towards the commitment, with no finding per line.

Each finding SHALL record:
- its severity: `rule_break` for `off_contract` and `overcharge`; `warning` for `missed_discount` and `price_unverifiable`; `info` otherwise;
- its amount, its expected and actual values, its quantity, its reason, and the judge's confidence.

#### Scenario: A laptop bought from a webshop

- **WHEN** an active agreement with Atea says IT equipment is bought from Atea, and a line "Dell Latitude 5450" for DKK 9,200 is invoiced by Proshop within the validity
- **THEN** there is an `off_contract` rule break of DKK 9,200 whose reason names the term, the "when in stock" condition, and Proshop

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
- the in-scope spend with the supplier in the current commitment period;
- the committed amount, and the target pro rata to today;
- a linear forecast to the end of the period;
- the rebate tier reached and the next one, when the term has tiers.

#### Scenario: Behind on a commitment

- **WHEN** a DKK 500,000 yearly commitment is at DKK 150,000 halfway through the year
- **THEN** progress shows DKK 150,000 against a pro-rata target of DKK 250,000, with a forecast of DKK 300,000

### Requirement: Findings SHALL be stored, refreshed by analysis runs, and keep their review

Findings SHALL be stored per term, line and kind. Each analysis run SHALL:
- recalculate the findings of every confirmed term;
- update the findings it produces again;
- delete the ones it no longer produces;
- delete every finding of rejected terms.

A finding's review SHALL survive re-analysis while the same term, line and kind is still produced. Its review status is `open`, `exception` or `not_in_scope`, with a note, who reviewed it and when.

A manager SHALL be able to review a finding through `PATCH /api/v1/agreement-findings/{id}`: mark it as an exception or as not in scope with a note, or reopen it. That SHALL be audited. Once any finding of a line against a term is marked `not_in_scope`, later runs SHALL NOT raise that line against that term, and SHALL keep that finding as the record of the decision.

#### Scenario: An accepted exception stays accepted

- **WHEN** a manager marks an off-contract finding as an exception ("Atea out of stock, urgent replacement") and analysis runs again
- **THEN** the finding is still an exception with that note

#### Scenario: Not in scope is learnt

- **WHEN** a manager marks a finding as not in scope
- **THEN** later runs don't raise that line against that term

### Requirement: Analysis SHALL run when terms or spend change, and on request

A company's `analyse_agreements` run SHALL be requested:
- when a term of one of its agreements is confirmed, or a confirmed term is edited or rejected;
- by the worker, as a system run, after the company's `sync`, `read_documents` or `categorize` run succeeds, when it has an active agreement;
- by a manager, through `POST /api/v1/companies/{id}/agreements/analyse`.

A request SHALL return the queued or running run of that kind rather than add another. The run's summary SHALL count:
- the terms analysed;
- the candidates, judged, cached and unjudged pairs;
- the findings by kind.

#### Scenario: New spend is checked

- **WHEN** a sync brings in new lines for a company with an active agreement
- **THEN** an `analyse_agreements` run is queued for it

### Requirement: The agreement report and the dashboard SHALL summarise findings

`GET /api/v1/agreements/{id}/report` SHALL return:
- the totals by kind and severity of the open findings: count and amount;
- the in-scope spend and the share of it with the supplier;
- commitment progress;
- the findings, filterable by kind and review status, rule breaks first. Each finding SHALL have its line's date, supplier, item and voucher.

`GET /api/v1/reports/agreement-compliance?from=&to=&company_id=` SHALL return, for the period and the caller's scope:
- the count and amount of open rule breaks;
- the off-contract spend;
- the overcharges;
- the five suppliers with the most off-contract spend.

#### Scenario: The report leads with rule breaks

- **WHEN** an agreement has two rule breaks, a warning and several compliant lines
- **THEN** the report's findings list the two rule breaks first, and its totals give their count and amount
