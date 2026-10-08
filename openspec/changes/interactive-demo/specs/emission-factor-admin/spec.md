## RENAMED Requirements

- FROM: `### Requirement: Only system admins SHALL manage emission factors`
- TO: `### Requirement: Every user SHALL read the emission factor status; only system admins SHALL manage emission factors`

## MODIFIED Requirements

### Requirement: Every user SHALL read the emission factor status; only system admins SHALL manage emission factors

`GET /api/v1/admin/emission-factors` (the status) SHALL be available to any
signed-in user of an organization. Every other endpoint under
`/api/v1/admin/emission-factors`, including the import history at `/imports`,
SHALL require a system admin. Any other caller SHALL get `403 Forbidden` and
change nothing.

#### Scenario: An organization member reads the status

- **WHEN** an organization member who is not a system admin requests the
  emission factor status
- **THEN** the response is 200 with the factor sets, the price indices and the
  coverage of their own organization's companies

#### Scenario: An organization admin is refused a write

- **WHEN** an organization admin who is not a system admin activates a factor
  set, refreshes a price index, uploads a workbook or lists the import history
- **THEN** the response is 403 and nothing changes

### Requirement: The status SHALL show the factor sets, the price indices and each company's matching coverage

`GET /api/v1/admin/emission-factors` SHALL return:

- `sets`: every factor set, active first and then newest imported first. Each
  set has its source, version, classification, currency, price year, price
  basis, attribution, number of sectors, number of factors, `imported_at` and
  `active`.
- `price_indices`: one entry for each price index mapped from an imported
  set's currency. Each has its series, label, number of months, latest month,
  and its average over the active set's price year (or none).
- `coverage`: for each company, its invoice lines counted as `ai`, `human`,
  `needs_review` or `unmatched`.

Coverage SHALL list every company for a system admin, and only the caller's
own organization's companies for anyone else.

In coverage:

- `ai` and `human` SHALL count only sectors in the active set's classification;
- `needs_review` SHALL count AI sectors below the review threshold, and those
  lines are also counted under `ai`;
- `unmatched` SHALL count lines with no sector or with a sector of another
  classification.

#### Scenario: Two releases, one active

- **WHEN** CEDA 2024 and CEDA 2025 are imported and CEDA 2025 is active
- **THEN** the status lists CEDA 2025 first as active, then CEDA 2024, each with its counts

#### Scenario: A price index not yet imported

- **WHEN** the active set is in USD and no CPI values are stored
- **THEN** `price_indices` lists `CPIAUCSL` with 0 months and no latest month

#### Scenario: Coverage counts

- **WHEN** a company has 10 lines: 6 matched by AI (1 below the review threshold), 2 chosen by a human and 2 without a sector
- **THEN** its coverage is 6 ai, 2 human, 1 needs review and 2 unmatched

#### Scenario: Coverage stays within the organization

- **WHEN** two organizations each have a company, and a member of the first
  requests the status
- **THEN** coverage lists only the first organization's company, while a system
  admin's request lists both
