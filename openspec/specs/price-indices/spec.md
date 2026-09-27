# price-indices Specification

## Purpose
Stores monthly values of named price index series (starting with US CPI-U from FRED), imports them from FRED or a file, and gives a year's average and a month's value so estimates can deflate spend to a factor set's price year.

## Requirements
### Requirement: Price indices SHALL be stored as monthly values of a named series

The system SHALL store price index values in `price_index_values`, one row per series and month:
- `series`: the series id, for example `CPIAUCSL`;
- `month`: the first day of the month the value is for;
- `value`: the index value;
- `source` and `imported_at`.

A series SHALL have at most one value per month. The index to deflate a factor set's currency with SHALL be looked up from that currency. US dollars SHALL map to `CPIAUCSL`, labelled "US CPI". Any other currency SHALL have no index until a mapping is added.

#### Scenario: One value per month

- **WHEN** a series is imported twice with a revised value for March 2026
- **THEN** the series has one March 2026 value, the revised one

#### Scenario: A currency with no index

- **WHEN** the index for EUR is looked up
- **THEN** there is none

### Requirement: A series SHALL be importable from FRED or a file

`python -m web_api.price_indices.import_series --series <id> [--file <csv>]` SHALL read a two-column CSV of dates and values. Without `--file`, it SHALL read FRED's public CSV for the series.

The import SHALL:
- skip rows whose value is blank or `.`;
- replace the series' stored values in one transaction;
- print the number of values and the latest month.

A CSV without a date column and a column named after the series SHALL fail, naming what is missing, and change nothing.

#### Scenario: Importing CPI from FRED

- **WHEN** the import runs for `CPIAUCSL` without `--file`
- **THEN** the series' monthly values are stored, and the count and latest month are printed

#### Scenario: A missing month is skipped

- **WHEN** the CSV's October 2025 row has no value
- **THEN** no October 2025 value is stored and the other months are

#### Scenario: A malformed file

- **WHEN** the file has no `CPIAUCSL` column
- **THEN** the import fails saying the column is missing, and the stored values are unchanged

### Requirement: A series SHALL give a year's average and a month's value

For a year, a series SHALL give the mean of its twelve monthly values, or none when any of the twelve is missing.

For a date, a series SHALL give the value for that date's month together with that month. When that month has no value, it SHALL give the latest earlier value and its month. For a date before the series' first value, it SHALL give none.

#### Scenario: A year's average

- **WHEN** a series has all twelve 2023 values
- **THEN** its 2023 average is their mean

#### Scenario: An incomplete year

- **WHEN** a series is missing one month of 2023
- **THEN** it has no 2023 average

#### Scenario: A gap is carried forward

- **WHEN** the value for 12 October 2025 is asked for and October 2025 has none
- **THEN** September 2025's value is given, with September 2025 as its month

#### Scenario: A month not yet published

- **WHEN** the value for a date in September 2026 is asked for and the latest value is August 2026
- **THEN** August 2026's value is given, with August 2026 as its month
