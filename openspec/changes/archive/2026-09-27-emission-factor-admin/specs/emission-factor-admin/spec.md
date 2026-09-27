## ADDED Requirements

### Requirement: Only system admins SHALL manage emission factors

Every endpoint under `/api/v1/admin/emission-factors` SHALL require a system admin. Any other caller, including an organization admin, SHALL get `403 Forbidden` and change nothing.

#### Scenario: An organization admin is refused

- **WHEN** an organization admin who is not a system admin requests the emission factor status
- **THEN** the response is 403

### Requirement: The status SHALL show the factor sets, the price indices and each company's matching coverage

`GET /api/v1/admin/emission-factors` SHALL return:
- `sets`: every factor set, active first and then newest imported first, with source, version, classification, currency, price year, price basis, attribution, number of sectors, number of factors, `imported_at` and `active`;
- `price_indices`: for each price index mapped from an imported set's currency, its series, label, number of months, latest month, and its average over the active set's price year (or none);
- `coverage`: for each company, its invoice lines counted as `ai`, `human`, `needs_review` or `unmatched`.

In coverage:
- `ai` and `human` SHALL count only sectors in the active set's classification;
- `needs_review` SHALL count AI sectors below the review threshold, and those lines are also counted under `ai`;
- `unmatched` SHALL count lines with no sector or with a sector of another classification.

#### Scenario: Two releases, one active

- **WHEN** CEDA 2024 and CEDA 2025 are imported and CEDA 2025 is active
- **THEN** the status lists CEDA 2025 first as active, then CEDA 2024, each with its counts

#### Scenario: A price index not yet imported

- **WHEN** the active set is in USD and no CPI values are stored
- **THEN** `price_indices` lists `CPIAUCSL` with 0 months and no latest month

#### Scenario: Coverage counts

- **WHEN** a company has 10 lines: 6 matched by AI (1 below the review threshold), 2 chosen by a human and 2 without a sector
- **THEN** its coverage is 6 ai, 2 human, 1 needs review and 2 unmatched

### Requirement: A system admin SHALL be able to activate an imported factor set

`POST /api/v1/admin/emission-factors/sets/{id}/activate` SHALL make that set the only active one in one transaction. It SHALL audit the change, naming the previously active set.

The response SHALL be the set, plus `rematch_needed`: true when the previously active set had a different classification. Activating the set that is already active SHALL change nothing and write no audit row. An unknown id SHALL get 404.

The CLI's `--activate` SHALL use the same activation.

#### Scenario: Switching releases

- **WHEN** a system admin activates CEDA 2024 while CEDA 2025 is active
- **THEN** CEDA 2024 is the only active set, estimates use it from the next read, and an audit row records the switch from CEDA 2025

#### Scenario: A different classification

- **WHEN** the newly active set's classification differs from the previous one's
- **THEN** the response has `rematch_needed` true

### Requirement: Imports SHALL run as recorded background jobs

Uploading a workbook and refreshing a price index SHALL each:
- create an import job with its kind, its file name or series, whether to activate, who asked and when;
- respond `202 Accepted` with the job;
- run it after the response.

A job SHALL move from `queued` to `running` to `succeeded` (with its counts) or `failed` (with its error). A failed job SHALL leave the stored factors and index values unchanged.

While a job of the same kind is `queued` or `running`, a new request of that kind SHALL get `409 Conflict`. When the web API starts, any job still `queued` or `running` SHALL be marked `failed` with the error "Interrupted by a restart".

`GET /api/v1/admin/emission-factors/imports?limit=` SHALL list the most recent jobs, newest first (default 20, max 100).

#### Scenario: A job's progress is visible

- **WHEN** a system admin refreshes CPI
- **THEN** the response is 202 with a queued job, and the job later shows `succeeded` with the number of months and the latest month

#### Scenario: One at a time

- **WHEN** a workbook import is running and another workbook is uploaded
- **THEN** the second upload gets 409 and no job is created

#### Scenario: A restart interrupts a job

- **WHEN** the web API restarts while a job is running
- **THEN** that job shows `failed` with "Interrupted by a restart"

### Requirement: A system admin SHALL be able to upload an Open CEDA workbook

`POST /api/v1/admin/emission-factors/workbooks` SHALL accept a multipart form with `file` and `activate`. It SHALL reject:
- a file whose name doesn't end in `.xlsx`, or that isn't a zip archive, with 422;
- a file larger than the configured limit (50 MB by default) with 413.

An accepted file SHALL be stored temporarily and imported by a job as the CLI imports it. With `activate` true, the set SHALL be activated when the import succeeds. The temporary file SHALL be deleted when the job ends, whether it succeeds or fails. A workbook that isn't an Open CEDA workbook SHALL fail the job, naming the missing sheet or label.

#### Scenario: A new release is uploaded and activated

- **WHEN** a system admin uploads the CEDA 2026 workbook with activate checked
- **THEN** the job succeeds with its sector, country, region and factor counts, CEDA 2026 is active, and the temporary file is gone

#### Scenario: The wrong spreadsheet

- **WHEN** an .xlsx without a `GHG_t_Raw` sheet is uploaded
- **THEN** the job fails naming the missing sheet, and the factor sets are unchanged

#### Scenario: Not a workbook

- **WHEN** a .pdf is uploaded
- **THEN** the response is 422 and no job is created

### Requirement: A system admin SHALL be able to refresh a price index

`POST /api/v1/admin/emission-factors/price-index/refresh` with `{"series": "CPIAUCSL"}` SHALL start a job that downloads the series from FRED and replaces its stored values, as the CLI does. A series that no factor set's currency maps to SHALL get 422.

#### Scenario: Refreshing CPI

- **WHEN** a system admin refreshes `CPIAUCSL` and FRED has published September 2026
- **THEN** the job succeeds, and the status shows September 2026 as the latest month

#### Scenario: FRED is unreachable

- **WHEN** the download fails
- **THEN** the job fails with the download error, and the stored values are unchanged
