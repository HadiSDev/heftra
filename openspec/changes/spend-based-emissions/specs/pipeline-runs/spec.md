## MODIFIED Requirements

### Requirement: A pipeline run is a stored record

The system SHALL store every requested or automatic pipeline run as a
`PipelineRun` row carrying: the company it runs for, its `kind`, its `status`,
who requested it, when it was requested, started and finished, a `summary` of
counts, and an `error` when it failed.

- `kind` SHALL be one of `sync` (sync from ERP), `read_documents` (read the
  company's pending documents), `categorize` (categorize the company's
  uncategorized lines) or `match_emissions` (match the company's lines to
  emission sectors).
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

### Requirement: The worker executes requested runs

`python -m ai_api.worker` SHALL be a long-running process that repeatedly
claims the oldest `queued` run, executes it, and records the outcome.

- Claiming SHALL be atomic: a run SHALL be moved from `queued` to `running` in a
  single conditional update, so two workers never execute the same run.
- A `sync` run SHALL sync every connected integration of the company exactly as
  `python -m ai_api.sync.runner --integration-id <id>` does.
- A `read_documents` run SHALL read the company's `pending` documents exactly as
  `python -m ai_api.documents.runner --company-id <id>` does, including the
  categorization of the lines each read creates.
- A `categorize` run SHALL categorize the company's `uncategorized` lines the
  way the sync's categorization step does, without contacting the ERP.
- A `match_emissions` run SHALL match the company's eligible lines to emission
  sectors exactly as `python -m ai_api.emissions.runner --company-id <id>` does.
  With no active factor set it SHALL succeed with a summary saying it was
  skipped.
- On success the run SHALL be `succeeded` with a `summary` of the counts the
  stage reports (for example lines categorized, documents read, failures).
- An exception SHALL mark the run `failed` with the error message, and the worker
  SHALL continue with the next run.
- When the worker starts, any run left `running` by a previous worker SHALL be
  marked `failed` with an error saying the worker stopped, so no run stays
  `running` forever.

#### Scenario: A queued run is executed

- **WHEN** a `categorize` run is `queued` and the worker polls
- **THEN** the run becomes `running`, the company's uncategorized lines are
  categorized, and the run ends `succeeded` with the number of lines categorized

#### Scenario: A queued emissions matching run is executed

- **WHEN** a `match_emissions` run is `queued`, a factor set is active, and the
  worker polls
- **THEN** the company's eligible lines are matched and the run ends `succeeded`
  with the matched, unmatched, cached and failed counts

#### Scenario: A failing run does not stop the worker

- **WHEN** a queued run raises during execution and another run is queued behind
  it
- **THEN** the first run is `failed` with its error and the second still runs

#### Scenario: Two workers never share a run

- **WHEN** two workers poll at the same moment with one run queued
- **THEN** exactly one of them executes it

#### Scenario: An interrupted run is not left running

- **WHEN** the worker starts and finds a run in `running`
- **THEN** that run is marked `failed` with an error saying the worker stopped
