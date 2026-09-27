## MODIFIED Requirements

### Requirement: A voucher's emissions SHALL be its posted spend split across its lines and multiplied by their factors

The system SHALL estimate a voucher's emissions in kg CO₂e in five steps:

1. **Spend.** Take the voucher's net expense posting in the company's base currency, the same amount Spend Lines shows.
2. **Split.** Split it across the voucher's invoice lines in proportion to their `base_amount`, in cents that add up to it exactly. A line with no sector and a negative amount (a discount) SHALL be left out of the weights, so the other lines absorb it.
3. **Convert.** Convert each line's share to the active factor set's currency at the rate for the voucher's date. The voucher's date is the earliest accounting date among its expense postings.
4. **Deflate.** Multiply each converted share by the price index for the factor set's currency: its average over the factor set's price year, divided by its value for the voucher's month, as the price-indices capability defines.
5. **Multiply.** Multiply each deflated share by the factor for the line's sector and supplier country.

When the factor set's currency has no index, or the index has no average for the price year or no value for the voucher's month, the Deflate step SHALL be skipped and the estimate SHALL be marked as not adjusted for inflation. That SHALL NOT change the voucher's `emissions_status`.

The **supplier's country** SHALL be the vendor's `country_code`, or else the country printed on the invoice. The factor lookup SHALL fall back to the company's country as the emission-factors capability defines.

A voucher's emissions SHALL be the sum over its estimated lines. Results SHALL be computed when read and not stored, so an edit, a new rate, a new index value or a new factor set changes them at once.

#### Scenario: A single-line voucher

- **WHEN** a voucher posted DKK 1,000.00 net to expense has one line matched to a sector whose factor for the supplier's country is 0.5 kg per USD, DKK 1,000.00 is USD 145.00 on the voucher's date, and the index averaged 300 in the price year and is 330 for the voucher's month
- **THEN** the voucher and the line are estimated at 65.909 kg CO₂e

#### Scenario: No index imported

- **WHEN** the same voucher is estimated with no index values stored
- **THEN** it is estimated at 72.500 kg CO₂e, marked as not adjusted for inflation, with status `estimated`

#### Scenario: The posted net, not the printed gross, is used

- **WHEN** a voucher's lines were printed VAT-inclusive at DKK 1,250.00 in total but the voucher posted DKK 1,000.00 net to expense
- **THEN** the lines share DKK 1,000.00 between them before conversion

#### Scenario: A discount is absorbed

- **WHEN** a voucher has a matched line of DKK 58.00 and an unmatched line of DKK −11.60, and posted DKK 46.40
- **THEN** the matched line's share is DKK 46.40 and the voucher is estimated in full

### Requirement: Each estimated line SHALL carry the calculation behind its emissions

Every estimated line in the voucher list and in a voucher's detail SHALL carry `emission_calculation`:
- `spend`: its share of the voucher's net spend, and `currency`, the base currency;
- `rate`, `rate_date` and `converted`: the exchange rate to the factor set's currency, the voucher date it was taken for, and the share converted;
- `deflation`: the index's `series` and `label`, the `month` whose value was used and that value as `index`, the `base_year` and its average as `base_index`, and `deflated`, the converted share × `base_index` ÷ `index`; or none when the estimate is not adjusted;
- `factor`, `factor_currency` and `factor_area`: the kg CO₂e per unit of the factor set's currency, that currency, and the country or region the factor is for;
- `sector`: the sector the factor belongs to;
- `kg_co2e`: the result, the deflated share (or the converted share when not adjusted) × `factor`.

The figures SHALL multiply out to `kg_co2e` to within rounding. A line that was not estimated SHALL carry no calculation.

#### Scenario: The calculation multiplies out

- **WHEN** a line's share is DKK 1,000.00, the rate to USD is 0.145, the index averaged 300 in 2023 and is 330 for the voucher's month, and the factor is 0.5 kg per USD
- **THEN** its calculation shows spend 1,000.00 DKK, rate 0.145, converted 145.00 USD, index 330 against a 2023 average of 300, deflated 131.82 USD, factor 0.5, and 65.909 kg CO₂e

#### Scenario: A carried-forward month is named

- **WHEN** a line's voucher is dated in October 2025 and the index has no October 2025 value
- **THEN** its calculation's `deflation.month` is September 2025

#### Scenario: The voucher detail carries it too

- **WHEN** a voucher with an estimated line is opened
- **THEN** that line in the detail carries the same calculation as in the list

## ADDED Requirements

### Requirement: The emissions summary and report SHALL name the price index used

The `factor_set` in `GET /api/v1/erp-entries/vouchers/emissions` and in `GET /api/v1/reports/spend-emissions` SHALL carry `price_index`: the index's `series`, its `label` and its `latest_month`. It SHALL be none when estimates are not adjusted for inflation, because the currency has no index or the index has no average for the price year.

#### Scenario: Adjusted figures

- **WHEN** US CPI is imported through August 2026 and the active set is in 2023 USD
- **THEN** `factor_set.price_index` is `CPIAUCSL`, "US CPI", with latest month August 2026

#### Scenario: Unadjusted figures

- **WHEN** no index values are stored
- **THEN** `factor_set.price_index` is none
