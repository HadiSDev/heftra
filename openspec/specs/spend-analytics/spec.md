# spend-analytics Specification

## Purpose
TBD - created by archiving change spend-dashboard. Update Purpose after archive.
## Requirements
### Requirement: Spend SHALL be the net expense the ERP posted, attributed by the lines' split

A voucher's spend SHALL be its net posting to expense accounts (debit less credit) in its company's base currency, dated by its accounting date. It SHALL be attributed to the voucher's supplier (the vendor of its invoice) and to categories by splitting it across the voucher's invoice lines in proportion to their base amounts: each line's share SHALL go to the line's category and subcategory, its second and third tree levels (`level_2`, `level_3`; the first level only splits direct from indirect spend), when the line is categorized (`ai_categorized` or `verified`), and to "Not categorized" otherwise. An uncategorized line below zero, such as a discount, SHALL take no share, so the voucher's other parts absorb it in proportion. A voucher with no invoice or no lines of positive total value SHALL be attributed wholly to "Not categorized" and, without an invoice, to no supplier. A voucher whose postings could not be converted SHALL be counted as unconverted and add no amount.

Attributed amounts of one voucher SHALL add up to its spend, so no figure built on them can exceed the spend it is part of.

#### Scenario: Lines printed with VAT

- **WHEN** a voucher posted 295.20 net and its only line reads 369.00 including VAT, categorized as Technology › Internet
- **THEN** 295.20 is attributed to Technology › Internet, not 369.00

#### Scenario: A voucher split across categories

- **WHEN** a voucher posted 430.46 and its lines are 484.00 Technology, 39.00 uncategorized and 15.07 Financial Services
- **THEN** Technology receives 387.20, Not categorized 31.20 and Financial Services 12.06, together 430.46

#### Scenario: A discount on the document

- **WHEN** a voucher posted 46.40 and its lines are 58.00 Travel › Ground Transport and an uncategorized discount of −11.60
- **THEN** all 46.40 is attributed to Travel › Ground Transport, and "Not categorized" receives nothing

#### Scenario: A posting with no invoice

- **WHEN** a bank fee is posted to an expense account with no invoice
- **THEN** its spend counts in the period's total, under "Not categorized" and no supplier

### Requirement: Spend reports SHALL be tenant-scoped, per base currency, over a period with a comparison

Every spend report SHALL take `from` and `to` dates (inclusive) and an optional `company_id`, SHALL cover only the caller's active companies (a foreign `company_id` is 404), and SHALL return figures per base currency, never summed across currencies. Where a report compares, a period starting on the first of a month SHALL be compared with the same days as many calendar months earlier (a month's last day matching the earlier month's last day), and any other period with as many days ending the day before `from`. `from` after `to` SHALL be 422.

#### Scenario: Another organization's spend

- **WHEN** two organizations have spend in the period
- **THEN** each sees only its own

#### Scenario: The comparison period

- **WHEN** the period is 2026-07-01 to 2026-09-30
- **THEN** the comparison period is 2026-04-01 to 2026-06-30

#### Scenario: A quarter so far

- **WHEN** the period is 2026-07-01 to 2026-09-26
- **THEN** the comparison period is 2026-04-01 to 2026-06-26

#### Scenario: A custom range

- **WHEN** the period is 2026-07-10 to 2026-07-19
- **THEN** the comparison period is 2026-06-30 to 2026-07-09

#### Scenario: Two base currencies

- **WHEN** the caller's companies keep DKK and SEK books
- **THEN** each report returns one set of figures for DKK and one for SEK

### Requirement: The overview SHALL give the period's spend, categorized share, suppliers and what needs attention

`GET /api/v1/reports/spend-overview` SHALL return per base currency: the period's spend and unconverted voucher count; the comparison period's spend; the spend of each of the twelve calendar months ending with the month of `to`; the categorized spend (the part attributed to a category); the number of suppliers with spend in the period and how many of them had no invoice to the caller before `from`. It SHALL also return, over the caller's scope and regardless of period, the number of lines needing review (AI-categorized below the review threshold), the number of invoices whose document failed to be read, and the number of invoices whose document total disagrees with the ERP beyond the reconciliation tolerance.

#### Scenario: Spend compared

- **WHEN** the period's spend is 12,000 and the comparison period's 10,000
- **THEN** the overview returns both, from which a 20% rise is shown

#### Scenario: A new supplier

- **WHEN** a supplier's first invoice to the caller falls inside the period
- **THEN** it counts as active and as new

### Requirement: The trend SHALL give monthly spend by the top categories

`GET /api/v1/reports/spend-trend` SHALL return per base currency the spend of each of the twelve calendar months ending with the month of `to`, split by category: the five categories with the most spend over those twelve months by name, and the rest together as "Other", with "Not categorized" apart. Months without spend SHALL be present with zero.

#### Scenario: A quiet month

- **WHEN** nothing was posted in March
- **THEN** March is in the trend with zero spend

#### Scenario: Many categories

- **WHEN** nine categories have spend
- **THEN** the five largest are named and the other four are summed as "Other"

### Requirement: The breakdown SHALL give spend by category and by supplier with their change

`GET /api/v1/reports/spend-breakdown` SHALL return per base currency: each category with its spend in the period, its spend in the comparison period and its subcategories with theirs, largest first; and the suppliers with the most spend in the period (default 10, at most 50 by `limit`) with their spend in both periods, name, country and id, largest first, ties broken by name.

#### Scenario: Categories with their children

- **WHEN** Technology has spend under Software and Hardware
- **THEN** Technology is returned with Software and Hardware beneath it, each with both periods' spend

#### Scenario: Top suppliers

- **WHEN** the caller had spend with 30 suppliers in the period
- **THEN** the ten largest are returned, each with its spend in both periods

### Requirement: Insights SHALL point at changes worth a look

`GET /api/v1/reports/spend-insights` SHALL return per base currency, each list at most five items:

- new suppliers: first invoice to the caller inside the period, with their spend in it;
- largest increases: suppliers whose spend rose most from the comparison period to the period, by amount, only rises, leaving out the new suppliers listed above;
- recurring suppliers: suppliers with spend in at least three of the six calendar months ending with the month of `to`, with their average spend over the months they had spend, largest first;
- largest uncategorized spend: the vouchers in the period with the most spend attributed to "Not categorized", with their supplier and invoice.

#### Scenario: A subscription

- **WHEN** a supplier has spend of about 400 in each of the last five months
- **THEN** it is listed as recurring with an average monthly spend of about 400

#### Scenario: A falling supplier

- **WHEN** a supplier's spend fell from the comparison period
- **THEN** it is not listed as an increase

