## MODIFIED Requirements

### Requirement: A pipeline run is a stored record

The system SHALL store every requested or automatic pipeline run as a
`PipelineRun` row carrying: the company it runs for, its `kind`, its `status`,
who requested it, when it was requested, started and finished, a `summary` of
counts, and an `error` when it failed.

- `kind` SHALL be one of `sync` (sync from ERP), `read_documents` (read the
  company's pending documents), `categorize` (categorize the company's
  uncategorized lines), `match_emissions` (match the company's lines to
  emission sectors) or `analyse_agreements` (check the company's spend lines
  against its agreements' confirmed terms).
- `status` SHALL move only `queued → running → succeeded | failed`. A run SHALL
  never move backwards, and a finished run SHALL never change again.
- `requested_by` SHALL be the requesting user's id, or `system` for a run the
  worker started on its own.
- Deleting a company SHALL delete its runs.

#### Scenario: A requested run starts queued

- **WHEN** a run is requested for a company
- **THEN** a `PipelineRun` exists for that company with status `queued`, the
  requesting user as `requested_by`, and no start or finish time

#### Scenario: A finished run is final

- **WHEN** a run has reached `succeeded` or `failed`
- **THEN** no later operation changes its status, times, summary or error

#### Scenario: An emissions matching run can be requested

- **WHEN** a system admin requests a run of kind `match_emissions`
- **THEN** a `queued` run of that kind is recorded

#### Scenario: An agreement analysis run is recorded

- **WHEN** an `analyse_agreements` run is requested for a company
- **THEN** a `queued` run of that kind is recorded for it

## ADDED Requirements

### Requirement: The worker SHALL read pending agreements on its own

When no run is queued, the worker SHALL claim and read one pending agreement, as it reads pending documents. A claim left `reading` longer than the stale timeout SHALL be claimable again.

After a company's `sync`, `read_documents` or `categorize` run succeeds, the worker SHALL queue a system `analyse_agreements` run for that company when it has an active agreement and no queued analysis.

#### Scenario: An uploaded agreement is read

- **WHEN** an agreement is `pending` and the worker has no queued run
- **THEN** the worker reads it, and it ends in `review` or `failed`

#### Scenario: Analysis follows a sync

- **WHEN** a sync run succeeds for a company with an active agreement
- **THEN** a system `analyse_agreements` run is queued for that company
