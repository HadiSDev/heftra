# frontend-emission-factor-admin Specification

## Purpose
The system-admin Emission factors page in Settings: the factor sets with an activate action, the price index with a refresh action, workbook upload, recent import jobs, and per-company matching coverage with an action to run matching.

## Requirements
### Requirement: System admins SHALL have an Emission factors page

The `/settings/emission-factors` Settings section SHALL show system admins:
- the factor sets;
- the price indices;
- an upload form for a workbook, with a drag-and-drop file picker;
- the recent import jobs;
- each company's matching coverage.

For anyone else it SHALL show a "System admins only" notice and SHALL NOT call the admin API. The page SHALL have its own loading, error and retry states.

#### Scenario: A system admin opens the page

- **WHEN** a system admin opens Emission factors
- **THEN** the page shows the factor sets with the active one marked, the CPI card, the upload form, the recent jobs and the coverage table

#### Scenario: Someone else follows the link

- **WHEN** an organization admin who is not a system admin opens `/settings/emission-factors`
- **THEN** the page says it is for system admins only, and no admin request is made

### Requirement: The factor sets SHALL be listed with an activate action

Each set SHALL show:
- its version, source, classification, price year and currency;
- its sector and factor counts;
- when it was imported;
- whether it is active.

A set that isn't active SHALL offer **Activate**. It SHALL open a confirmation that names the current and the new set, says every estimate will change, and warns that lines will need matching again when the classifications differ. After activation, the page SHALL refresh the status and the app's emissions figures.

#### Scenario: Activating an older release

- **WHEN** a system admin activates CEDA 2024 and confirms
- **THEN** CEDA 2024 is shown as active, and the dashboard and Spend Lines show figures from CEDA 2024 on their next load

### Requirement: The price index SHALL be shown with a refresh action

The price index card SHALL show:
- the series label and id;
- the number of months and the latest month;
- the active set's base-year average.

It SHALL say "Not imported, so estimates are not adjusted for inflation" when the index has no values. **Refresh from FRED** SHALL start a refresh job, and SHALL be disabled while one is queued or running.

#### Scenario: Refreshing

- **WHEN** a system admin clicks Refresh from FRED
- **THEN** a job appears as queued and then running, and when it succeeds the card shows the new latest month

### Requirement: A workbook SHALL be uploadable with a choice to activate it

The upload form SHALL take one `.xlsx` file, dropped or browsed for with the UI library's file dropzone, and an **Activate when imported** checkbox. It SHALL show the upload's progress.

It SHALL refuse a file that isn't `.xlsx`, or that is over the limit, before uploading, and it SHALL show the server's refusal when there is one. It SHALL be disabled while a workbook job is queued or running.

#### Scenario: Uploading a release

- **WHEN** a system admin chooses a workbook, checks Activate when imported, and uploads
- **THEN** the form shows the upload's progress, then a queued job, and the sets list shows the new release once the job succeeds

### Requirement: Recent import jobs SHALL show their progress and outcome

The jobs list SHALL show each job's:
- kind and file or series;
- status;
- who asked;
- when it started and how long it took;
- its counts or its error.

While any job is queued or running, the list SHALL refresh every few seconds. When a job finishes, the page SHALL refresh the status.

#### Scenario: A failed import explains itself

- **WHEN** a workbook job fails because a sheet is missing
- **THEN** its row shows failed with the missing sheet's name

### Requirement: Coverage SHALL show each company's matching and offer to run it

The coverage table SHALL show, for each company:
- its lines matched by AI, chosen by a person, needing review, and unmatched;
- a bar of the matched share.

A **Match emission sectors** action SHALL request the company's `match_emissions` run, and report that it was requested or why not.

#### Scenario: Matching a company

- **WHEN** a system admin clicks Match emission sectors for a company with unmatched lines
- **THEN** a matching run is requested, and the action says so
