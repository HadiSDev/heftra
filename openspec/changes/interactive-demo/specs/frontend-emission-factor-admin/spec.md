## RENAMED Requirements

- FROM: `### Requirement: System admins SHALL have an Emission factors page`
- TO: `### Requirement: Everyone SHALL have an Emission factors page, and system admins SHALL manage it`

## MODIFIED Requirements

### Requirement: Everyone SHALL have an Emission factors page, and system admins SHALL manage it

The `/settings/emission-factors` Settings section SHALL show system admins:

- the factor sets;
- the price indices;
- an upload form for a workbook, with a drag-and-drop file picker;
- the recent import jobs;
- each company's matching coverage.

Anyone else SHALL see a read-only version. It shows:

- the factor sets with the active one marked;
- the price indices;
- their own organization's companies' coverage.

It SHALL show no activate, refresh, upload, import jobs or match controls, and
SHALL NOT request the import history. The page SHALL have its own loading,
error and retry states.

#### Scenario: A system admin opens the page

- **WHEN** a system admin opens Emission factors
- **THEN** the page shows the factor sets with the active one marked, the CPI card, the upload form, the recent jobs and the coverage table

#### Scenario: Someone else opens the page

- **WHEN** an organization member who is not a system admin opens
  `/settings/emission-factors`
- **THEN** the page shows the factor sets, the price index card and their
  companies' coverage, with no Activate, Refresh from FRED, upload, jobs or
  Match emission sectors controls, and no request for the import history

### Requirement: Coverage SHALL show each company's matching and offer to run it

The coverage table SHALL show, for each company:

- its lines matched by AI, chosen by a person, needing review, and unmatched;
- a bar of the matched share.

For system admins, a **Match emission sectors** action SHALL request the
company's `match_emissions` run, and report that it was requested or why not.
The read-only page SHALL NOT show this action.

#### Scenario: Matching a company

- **WHEN** a system admin clicks Match emission sectors for a company with unmatched lines
- **THEN** a matching run is requested, and the action says so
