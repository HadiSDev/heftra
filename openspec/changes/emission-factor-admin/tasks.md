## 0. Before starting

- [ ] 0.1 Archive `spend-based-emissions` and `emissions-inflation-adjustment` (with the user's go-ahead)
- [x] 0.2 Declare `python-multipart` in web-api's dependencies (the user runs the sync)

## 1. Jobs and activation (web-api)

- [x] 1.1 `ReferenceDataImport` model (`db/models/reference_data_import.py`) with the `ReferenceImportKind` and `ReferenceImportStatus` enums. Migration `0019_reference_data_imports`; do not run it
- [x] 1.2 `emissions/activation.py`: `activate_factor_set(session, factor_set, actor) -> ActivationResult` (the previous set, `rematch_needed`), with an audit row and a no-op when the set is already active. `import_workbook(--activate)` uses it (tests)
- [x] 1.3 `reference_imports/jobs.py`: create a job, refuse one while the same kind is queued or running, and mark running, succeeded (with a result) or failed (with an error) (tests)
- [x] 1.4 `reference_imports/runners.py`: `run_workbook_job(job_id, path)` (reads, imports, optionally activates, always deletes the file) and `run_price_index_job(job_id, series)`, each in its own session (tests with a generated workbook and a stubbed download)
- [x] 1.5 `reference_imports/uploads.py`: stream an upload to a temp file with a size limit, checking the `.xlsx` name and the zip signature (tests: too large, wrong type)
- [x] 1.6 Mark queued or running jobs as interrupted on app startup (test)
- [x] 1.7 Config: `UPLOAD_TMP_DIR` and `EMISSION_WORKBOOK_MAX_BYTES`, documented in `.env.example`

## 2. Admin API (web-api)

- [x] 2.1 Schemas in `schemas/admin/`: the factor set row, the price index row, coverage, status, job, activation result
- [x] 2.2 `admin/emission_status.py`: sets with counts, price indices, and coverage per company in one grouped query (tests for each count, including another classification and the review threshold)
- [x] 2.3 `routers/admin_emission_factors.py`: GET status, POST activate, POST price-index refresh, POST workbooks, GET imports, each depending on `require_system_admin`. Register it in `app.py`
- [x] 2.4 API tests:
  - [x] 2.4.1 403 for an org admin on every route
  - [x] 2.4.2 Activate: switches, audits, no-op, 404, `rematch_needed`
  - [x] 2.4.3 Refresh: 202, then succeeded, and failed with the download error
  - [x] 2.4.4 Upload: 202 and imported and activated; 413; 422; 409 while one is running
  - [x] 2.4.5 Imports list: order and limit

## 3. Web

- [ ] 3.1 Types and queries in `lib/api/admin-emission-factors.ts`:
  - [ ] 3.1.1 The status query, and the jobs query (refetching every 2 s while a job is active)
  - [ ] 3.1.2 Mutations for activate, refresh and upload (upload with progress via XHR), each invalidating the status and the emissions queries
- [ ] 3.2 `AppSidebar` gets a `SidebarFooter` for system admins with a "System" caption and `ADMIN_NAV_ITEMS` (Emission factors, `Leaf`) (tests: shown to system admins, hidden from others, active marking)
- [ ] 3.3 Route `routes/_authed/admin/emission-factors.tsx`, titled "Emission factors", with the non-system-admin notice (test)
- [ ] 3.4 Components in `components/admin/emission-factors/`:
  - [ ] 3.4.1 `factor-sets-table`
  - [ ] 3.4.2 `activate-dialog`
  - [ ] 3.4.3 `price-index-card`
  - [ ] 3.4.4 `workbook-upload`
  - [ ] 3.4.5 `import-jobs`
  - [ ] 3.4.6 `coverage-table` with the Match emission sectors action
  - [ ] 3.4.7 Loading, error and empty states
  - [ ] 3.4.8 Tests
- [ ] 3.5 Run vitest, tsc, eslint and prettier on the changed files

## 4. Verification

- [ ] 4.1 Run the web-api suite in full
- [ ] 4.2 With the user's go-ahead, after the migration: as an impersonated system admin, refresh CPI, and activate and re-activate CEDA 2025. Check that the sidebar footer shows only for system admins
- [ ] 4.3 Upload the real Open CEDA 2025 workbook as a re-import, and check that the job's counts match the CLI's
