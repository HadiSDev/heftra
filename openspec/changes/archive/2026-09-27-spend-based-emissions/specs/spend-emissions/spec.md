## ADDED Requirements

### Requirement: A voucher's emissions SHALL be its posted spend split across its lines and multiplied by their factors

The system SHALL estimate a voucher's emissions in kg CO₂e in four steps:

1. **Spend.** Take the voucher's net expense posting in the company's base currency, the same amount Spend Lines shows.
2. **Split.** Split it across the voucher's invoice lines in proportion to their `base_amount`, in cents that add up to it exactly. A line with no sector and a negative amount (a discount) SHALL be left out of the weights, so the other lines absorb it.
3. **Convert.** Convert each line's share to the active factor set's currency at the rate for the voucher's date. The voucher's date is the earliest accounting date among its expense postings.
4. **Multiply.** Multiply each converted share by the factor for the line's sector and supplier country.

The **supplier's country** SHALL be the vendor's `country_code`, or else the country printed on the invoice. The factor lookup SHALL fall back to the company's country as the emission-factors capability defines.

A voucher's emissions SHALL be the sum over its estimated lines. Results SHALL be computed when read and not stored, so an edit, a new rate or a new factor set changes them at once.

#### Scenario: A single-line voucher

- **WHEN** a voucher posted DKK 1,000.00 net to expense has one line matched to a sector whose factor for the supplier's country is 0.5 kg per USD, and DKK 1,000.00 is USD 145.00 on the voucher's date
- **THEN** the voucher and the line are estimated at 72.500 kg CO₂e

#### Scenario: The posted net, not the printed gross, is used

- **WHEN** a voucher's lines were printed VAT-inclusive at DKK 1,250.00 in total but the voucher posted DKK 1,000.00 net to expense
- **THEN** the lines share DKK 1,000.00 between them before conversion

#### Scenario: A discount is absorbed

- **WHEN** a voucher has a matched line of DKK 58.00 and an unmatched line of DKK −11.60, and posted DKK 46.40
- **THEN** the matched line's share is DKK 46.40 and the voucher is estimated in full

### Requirement: What could not be estimated SHALL be counted with its reason

Each voucher SHALL have an `emissions_status`:
- `estimated`: every line was estimated.
- `partial`: some lines were.
- One reason when none were:
  - `no_spend`: the voucher posted no net expense.
  - `no_lines`: the voucher has no invoice lines.
  - `unmatched`: no line has a sector.
  - `no_factor`: no factor for any country tried.
  - `unconverted`: no exchange rate to the factor set's currency for the voucher's date.
  - `no_factor_set`: no factor set is active.

A failed rate lookup SHALL mark the voucher `unconverted` and SHALL NOT fail the request.

#### Scenario: A journal-only voucher

- **WHEN** a voucher has expense postings but no invoice lines
- **THEN** its emissions are empty and its status is `no_lines`

#### Scenario: Half the lines are matched

- **WHEN** a voucher has two equal lines and only one has a sector with a factor
- **THEN** its status is `partial` and its emissions come from that line's half of the spend

#### Scenario: No rate

- **WHEN** no rate to the factor set's currency can be found for the voucher's date
- **THEN** the voucher's status is `unconverted` and the voucher list still loads

### Requirement: The voucher list SHALL carry each voucher's and each line's emissions

`GET /api/v1/erp-entries/vouchers` SHALL include:
- **on each voucher:** `kg_co2e` (empty when nothing was estimated) and `emissions_status`;
- **on each line:**
  - `emission_sector` as `{id, code, name}`, or empty;
  - `emission_sector_source`, `emission_sector_confidence` and `emission_sector_rationale`;
  - `kg_co2e`;
  - `emission_area`, the country or region whose factor was used.

Amounts of kg SHALL be given to three decimals.

#### Scenario: A listed voucher shows its emissions

- **WHEN** the voucher list includes an estimated voucher
- **THEN** the voucher has its `kg_co2e` and status `estimated`, and each line has its sector, its kg and the area whose factor was used

### Requirement: Spend Lines' emissions SHALL be summarized under its filters

`GET /api/v1/erp-entries/vouchers/emissions` SHALL accept the same filters as `GET /api/v1/erp-entries/vouchers/summary` and SHALL return:
- `factor_set`: the active set's source, version, currency, price year, price basis and attribution, or empty when none is active;
- `kg_co2e`: the total over the filtered vouchers;
- per base currency, `posted_spend` and `estimated_spend`;
- the number of vouchers with each `emissions_status`.

It SHALL be scoped to the caller's companies exactly as the voucher list is. It SHALL respond `404 Not Found` for a company the caller cannot see.

#### Scenario: Filters narrow the total

- **WHEN** the summary is requested for one supplier
- **THEN** its total and spend figures cover only that supplier's vouchers

#### Scenario: No factor set

- **WHEN** no factor set is active
- **THEN** the summary has an empty `factor_set`, no total, and every voucher counted as `no_factor_set`

### Requirement: Emission sectors SHALL be searchable

`GET /api/v1/emission-sectors?q=<text>&limit=<n>` SHALL return sectors of the active factor set's classification whose code or name contains the text, ignoring case. It SHALL return at most `limit` sectors (default 20, at most 50), each as `{id, code, name}`, ordered by name. Any signed-in user SHALL be able to search. With no active set it SHALL return an empty list.

#### Scenario: Searching by name

- **WHEN** a user searches for "computer"
- **THEN** the sectors whose names contain "computer" are returned, at most 20

### Requirement: A human SHALL be able to set or clear a line's emission sector

`PATCH /api/v1/invoice-lines/{id}` SHALL accept `emission_sector_id`.

- **Setting a sector** SHALL store it with source `human` and no confidence or rationale.
- **Clearing it** (null) SHALL remove the sector, source, confidence and rationale, so the matcher may match the line again.
- A sector outside the active set's classification SHALL be refused with `422 Unprocessable Entity`, and nothing changed.
- The change SHALL be written to the audit log with the old and new sector, like other line edits.
- The same permissions SHALL apply as to other line edits.

#### Scenario: A reviewer corrects a sector

- **WHEN** a reviewer sets a line's sector to another sector of the active classification
- **THEN** the line has that sector with source `human`, the audit log records the change, and the voucher's emissions reflect it on the next read

#### Scenario: A sector of another classification is refused

- **WHEN** a reviewer sends a sector id from a classification that is not active
- **THEN** the API responds `422` and the line is unchanged

### Requirement: Each estimated line SHALL carry the calculation behind its emissions

Every estimated line in the voucher list and in a voucher's detail SHALL carry `emission_calculation`:
- `spend`: its share of the voucher's net spend, and `currency`, the base currency;
- `rate`, `rate_date` and `converted`: the exchange rate to the factor set's currency, the voucher date it was taken for, and the share converted;
- `factor`, `factor_unit` and `factor_area`: the kg CO₂e per unit of the factor set's currency, what that unit is, and the country or region the factor is for;
- `sector`: the sector the factor belongs to;
- `kg_co2e`: the result, `converted` × `factor`.

The figures SHALL multiply out to `kg_co2e` to within rounding. A line that was not estimated SHALL carry no calculation.

#### Scenario: The calculation multiplies out

- **WHEN** a line's share is DKK 1,000.00, the rate to USD is 0.145 and the factor is 0.5 kg per USD
- **THEN** its calculation shows spend 1,000.00 DKK, rate 0.145, converted 145.00 USD, factor 0.5, and 72.500 kg CO₂e

#### Scenario: The voucher detail carries it too

- **WHEN** a voucher with an estimated line is opened
- **THEN** that line in the detail carries the same calculation as in the list

### Requirement: The dashboard's emissions SHALL be reported for a period

`GET /api/v1/reports/spend-emissions?from=&to=&company_id=` SHALL take the same scope as the other spend reports. It SHALL return:
- `factor_set`: the active set's details, or empty when none is active;
- `kg_co2e` for the period, and `comparison_kg_co2e` for its comparison period;
- the twelve months ending with the period, each with its kg;
- per base currency, the posted and estimated spend in the period;
- the five sectors with the most emissions in the period, each with its kg.

A voucher SHALL fall in the month and period of its date, as in the other spend reports.

#### Scenario: A period's emissions and their change

- **WHEN** a company's vouchers are estimated at 30 kg in September and 20 kg in August, and September is asked for
- **THEN** the report gives 30 kg for the period, 20 kg for the comparison, and both months in its twelve

#### Scenario: No factor set

- **WHEN** no factor set is active
- **THEN** the report has an empty `factor_set` and no figures
