# emission-factors Specification

## Purpose
Imports and stores versioned emission factor sets (starting with Open CEDA), their sectors and per-country factors, keeps exactly one set active, and looks up a factor by sector and country with regional and company-country fallback, carrying the source's licence attribution.

## Requirements
### Requirement: Emission factors SHALL be stored as versioned factor sets

The system SHALL store spend-based emission factors in three tables:
- `emission_factor_sets`, one row per imported release, carrying:
  - `source` and `version`;
  - `classification` (the sector scheme its factors are keyed by);
  - `currency` and `price_year` (the money its factors are per unit of);
  - `price_basis` (`purchaser`: per unit of money the buyer paid);
  - `licence` and `attribution`;
  - `imported_at` and `active`.
- `emission_sectors`, one row per sector of a classification: `classification`, `code`, `name` and `description`, unique on (`classification`, `code`).
- `emission_factors`, one row per (factor set, sector, area), carrying `kg_co2e_per_unit`. The area is either a country (an ISO 3166-1 alpha-2 code) or a region name, never both.
- `emission_country_regions`, mapping each country to its region within a set.

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

`python -m web_api.emissions.import_factors --file <path> [--activate]` SHALL read an Open CEDA workbook into a factor set with:
- source `open_ceda`;
- the classification `ceda-bea`, and the version, currency and price year the workbook states, with price basis `purchaser`;
- the attribution "CEDA by Watershed" and the licence "CC BY-SA 4.0".

- Sheets SHALL be found by their names, and columns by their header labels. A missing sheet or label SHALL fail the import with a message naming it, and write nothing.
- It SHALL read:
  - the country factors from `GHG_t_Raw`;
  - the region averages from `Regional Average EFs`, and the `ROW` row of `GHG_t_Raw` as the region "Rest of World";
  - the country-to-region map from `Country to region mapping`;
  - the sectors, with their descriptions, from `Metadata`;
  - the version from the Cover sheet.
- It SHALL NOT read `GHG_t`, whose values depend on the workbook's saved selectors.
- It SHALL convert each producer-price factor to a purchaser-price factor by multiplying it by its sector's ratio from `Purchaser - producer conversion`, and SHALL store the set with price basis `purchaser`.
- Countries SHALL be stored as ISO alpha-2 codes, converted from the workbook's alpha-3 codes. Codes that cannot be converted SHALL be reported and skipped.
- Importing a version that already exists SHALL replace that set's factors rather than add a second set.
- The whole import SHALL be one transaction.
- It SHALL print the number of sectors, countries and factors written.

#### Scenario: A workbook is imported and activated

- **WHEN** the importer runs on a valid workbook with `--activate`
- **THEN** a set with source `open_ceda` exists, is active, has a factor per sector and country in the workbook, and the counts are printed

#### Scenario: A renamed sheet fails the import

- **WHEN** the workbook lacks an expected sheet or header label
- **THEN** the importer exits non-zero naming it, and no set or factor is written

#### Scenario: Factors are converted to purchaser prices

- **WHEN** a sector's producer-price factor for Denmark is 0.1 kg per USD and its purchaser-to-producer ratio is 0.8
- **THEN** the stored Denmark factor for that sector is 0.08 kg per USD, and the set's price basis is `purchaser`

#### Scenario: Re-importing a version replaces it

- **WHEN** the same version is imported twice
- **THEN** there is one set for that version, holding the second import's factors

### Requirement: A factor SHALL be looked up by sector and country, falling back to regions and the company's country

Looking up a factor for a sector SHALL try, in order:
1. the supplier's country;
2. the supplier's country's region;
3. the company's country;
4. the company's country's region;
5. the rest-of-world average, when the set has one.

It SHALL return the factor together with the country or region it came from. When none has a factor, it SHALL return no factor.

#### Scenario: The supplier's country has a factor

- **WHEN** a sector has factors for DE and DK, the supplier is German and the company Danish
- **THEN** the DE factor is used and the area is reported as DE

#### Scenario: A supplier country without its own factors

- **WHEN** the supplier is in Taiwan, which has no country factors but is mapped to "Eastern Asia"
- **THEN** the Eastern Asia average is used and that region is reported

#### Scenario: Falling back to the company's country

- **WHEN** the supplier has no country and the company is Danish
- **THEN** the DK factor is used

#### Scenario: No factor anywhere

- **WHEN** neither the supplier's nor the company's country or region has a factor for the sector, and the set has no rest-of-world factor for it
- **THEN** no factor is returned
