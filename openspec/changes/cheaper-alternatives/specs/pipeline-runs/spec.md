## MODIFIED Requirements

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
- A `find_alternatives` run SHALL find the alternatives of the one item named
  in its parameters, from every enabled source (see `product-alternatives`),
  extracting the item's specification first when it has none.
- A `scan_alternatives` run SHALL find the alternatives of the company's
  largest-spend items that are due, as the background scan does (see
  `product-alternatives`), and SHALL be requested by the worker itself.
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
  with the agent, fallback, unmatched, cached and failed counts

#### Scenario: A queued alternatives search is executed

- **WHEN** a `find_alternatives` run is `queued` for an item and the worker polls
- **THEN** the item's alternatives are found and the run ends `succeeded` with
  the number of candidates read and alternatives found per source

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
