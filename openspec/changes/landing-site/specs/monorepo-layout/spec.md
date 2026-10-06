## MODIFIED Requirements

### Requirement: Every runnable app lives under apps/

The repository SHALL place each runnable application in its own directory under
`apps/`: `apps/web` (the frontend), `apps/landing` (the public marketing site),
`apps/web-api` (the business domain and customer API, import name `web_api`),
`apps/ai-api` (the AI workflows, import name `ai_api`) and `apps/mock-erp` (the
standalone mock ERP server, import name `mock_erp`). The repository root SHALL NOT
contain application source: no `src/`, no `frontend/`, no `mock_erp/`. The root
keeps only workspace-level files (workspace manifest, lockfile, compose file,
docs, OpenSpec, shared `data/`).

#### Scenario: Old locations are gone

- **WHEN** the repository root is listed after the change
- **THEN** it contains `apps/` with exactly `web`, `landing`, `web-api`, `ai-api`
  and `mock-erp`, and contains no `src/`, `frontend/` or `mock_erp/` directory

#### Scenario: Import names are unchanged

- **WHEN** application code imports `web_api`, `ai_api` or `mock_erp`
- **THEN** the import resolves without modification to the import statement

#### Scenario: The landing site is independent

- **WHEN** `apps/landing` is installed and built on its own
- **THEN** it needs neither the Python workspace nor `apps/web`'s dependencies
