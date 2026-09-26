## ADDED Requirements

### Requirement: Emission factors SHALL be stored as versioned factor sets

The system SHALL store spend-based emission factors in three tables:
- `emission_factor_sets`, one row per imported release, carrying:
  - `source` and `version`;
  - `classification` (the sector scheme its factors are keyed by);
  - `currency` and `price_year` (the money its factors are per unit of);
  - `gwp` (the global warming potential basis);
  - `licence` and `attribution`;
  - `imported_at` and `active`.
- `emission_sectors`, one row per sector of a classification: `classification`, `code` and `name`, unique on (`classification`, `code`).
- `emission_factors`, one row per (factor set, sector, country), carrying `kg_co2e_per_unit`. The country is an ISO 3166-1 alpha-2 code.

Sectors SHALL belong to a classification, not to a set, so a later release of the same classification reuses them.

#### Scenario: A second release reuses the sectors

- **WHEN** two releases of the same classification are imported
- **THEN** each has its own factors, and both refer to the same `emission_sectors` rows

#### Scenario: One factor per sector and country in a set

- **WHEN** an import holds two factors for the same sector and country
- **THEN** the import fails and names the duplicate, and nothing is written

### Requirement: Exactly one factor set SHALL be active at a time

At most one factor set SHALL be `active`, and every emission estimate and sector match SHALL use that set. Activating a set SHALL deactivate every other set in the same transaction. When no set is active, the system SHALL report that no factors are imported rather than estimating with any set.

#### Scenario: Activating a new release

- **WHEN** a set is active and a newer release is imported with `--activate`
- **THEN** only the newer release is active afterwards

#### Scenario: No active set

- **WHEN** no factor set is active
- **THEN** emission estimates report that no factors are imported, and no figure is computed

### Requirement: The Open CEDA workbook SHALL be importable from the command line

`python -m web_api.emissions.import_factors --file <path> --version <version> [--activate]` SHALL read an Open CEDA workbook into a factor set with:
- source `open_ceda`;
- the classification, currency, price year and GWP basis the workbook states;
- the attribution "CEDA by Watershed" and the licence "CC BY-SA 4.0".

- Columns SHALL be found by their header names. A missing expected column SHALL fail the import with a message naming it, and write nothing.
- Countries SHALL be stored as ISO alpha-2 codes. Countries the workbook names that cannot be mapped to a code SHALL be reported and skipped.
- Importing a version that already exists SHALL replace that set's factors rather than add a second set.
- The whole import SHALL be one transaction.
- It SHALL print the number of sectors, countries and factors written.

#### Scenario: A workbook is imported and activated

- **WHEN** the importer runs on a valid workbook with `--activate`
- **THEN** a set with source `open_ceda` exists, is active, has a factor per sector and country in the workbook, and the counts are printed

#### Scenario: A renamed column fails the import

- **WHEN** the workbook lacks an expected column
- **THEN** the importer exits non-zero naming the column, and no set or factor is written

#### Scenario: Re-importing a version replaces it

- **WHEN** the same version is imported twice
- **THEN** there is one set for that version, holding the second import's factors

### Requirement: A factor SHALL be looked up by sector and country, with the company's country as fallback

Looking up a factor for a sector SHALL try, in order:
1. the supplier's country;
2. the company's country.

It SHALL return the factor together with the country it came from. When neither country has a factor, it SHALL return no factor.

#### Scenario: The supplier's country has a factor

- **WHEN** a sector has factors for DE and DK, the supplier is German and the company Danish
- **THEN** the DE factor is used and the country is reported as DE

#### Scenario: Falling back to the company's country

- **WHEN** the supplier's country has no factor for the sector but the company's does
- **THEN** the company's country's factor is used and that country is reported

#### Scenario: No factor for either country

- **WHEN** neither the supplier's nor the company's country has a factor for the sector
- **THEN** no factor is returned
