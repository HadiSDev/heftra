## Context

- **Factor sets** are imported by `web_api.emissions.import_factors`:
  - `read_workbook(path)` parses the Open CEDA workbook with openpyxl;
  - `import_workbook(session, workbook, activate=)` writes about 400 sectors and 68,000 factors in one transaction.
- **The price index** is imported by `web_api.price_indices.import_series`:
  - `download_series_csv`, then `parse_series_csv`, then `replace_series`.
- **System admins** are gated by `auth.deps.require_system_admin`, and `principal.isSystemAdmin` on the web.
- **Settings** (`routes/_authed/settings.tsx`) renders a fixed list of tabs; system-admin-only controls elsewhere, such as the company Run menu, check `principal.isSystemAdmin`.
- **Pipeline runs** are per company (`company_id` NOT NULL) and executed by the ai-api worker. Factor imports are global and web-api code, so they don't fit there.
- **Upload handling:** the web API has no file upload yet.

## Goals / Non-Goals

**Goals:**
- A system admin can see the reference data's state, switch the active set, refresh CPI and load a new workbook without a shell.
- Long imports don't block a request, and their outcome is visible afterwards.
- Keep system-admin controls in Settings, next to the other management pages, rather than in the main navigation.

**Non-Goals:**
- Deleting or editing factor sets, sectors or factors.
- Scheduling.
- A job queue shared with pipeline runs.
- Customer-admin access. This is platform data, so system admins only.

## Decisions

### A small `reference_data_imports` table, run in the web API process

Each upload or refresh gets a row:
- `id`, `kind` (`factor_workbook` | `price_index`), `status` (`queued` | `running` | `succeeded` | `failed`);
- `filename` or `series`, and `activate` (bool);
- `result` (JSON counts), `error`;
- `requested_by`, `requested_at`, `started_at`, `finished_at`.

The request stores the row and schedules the work with FastAPI `BackgroundTasks`, which opens its own `Session(engine)`. It returns `202` with the job.

Before writing, the job re-checks that no other job of the same kind is running. It also refuses to queue a second one while one is queued or running (`409`), because two imports into the same version would fight over its factors.

On startup, any job still `queued` or `running` is marked `failed` with "Interrupted by a restart".

*Alternatives considered:*
- **Make `pipeline_runs.company_id` nullable and add a kind for the ai-api worker.** That puts web-api import code into ai-api's worker, and turns every run query into company-or-global. Rejected.
- **Run the import inside the request.** A 68,000-factor workbook takes long enough to hit proxy timeouts, and the user gets no record. Rejected.
- **Celery or RQ.** A new dependency and service for a few imports a year. Rejected.

### Upload to a temporary file, deleted when the job ends

- The upload is streamed to `tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)` in `config.UPLOAD_TMP_DIR` (default: the system temp dir), up to `EMISSION_WORKBOOK_MAX_BYTES` (50 MB).
- It is rejected with `413` above that, and with `422` for a name not ending `.xlsx` or content that isn't a zip.
- The job reads the file and deletes it in a `finally`. Nothing is kept: the workbook is public and can be re-downloaded.
- `read_workbook` errors (a missing sheet or label) become the job's `error`, and the database is untouched because `import_workbook` runs in one transaction.

### Activation is its own endpoint, sharing the importer's rule

`POST /admin/emission-factors/sets/{id}/activate` deactivates the others and activates this one in one transaction. It writes an `AuditLog` row: entity `emission_factor_set`, action `activate`, with `active` changing from false to true and the previously active set's id.

The importer's `--activate` path uses the same function, moved to `emissions/activation.py`, so there is one rule. Activating a set of a different classification is allowed. The response warns that its lines will need matching again, and the page says so in the confirmation.

### Coverage is counted, not estimated

Per company, count `invoice_lines` grouped by:
- AI sector in the active classification;
- human sector;
- AI with confidence below the review threshold (the same `emission_needs_review` rule);
- no sector, or a sector of another classification.

This is one grouped query joining `emission_sectors`. Emissions totals stay on the dashboard; this page is about data readiness.

### API shape

All routes are under `/api/v1/admin/emission-factors`, and every one depends on `require_system_admin`:

| Method | Path | Returns |
|---|---|---|
| GET | `` | `{sets: [...], price_indices: [...], coverage: [...]}` |
| POST | `/sets/{id}/activate` | the updated set, plus `rematch_needed` |
| POST | `/price-index/refresh` `{series}` | 202 + the job |
| POST | `/workbooks` (multipart: `file`, `activate`) | 202 + the job |
| GET | `/imports?limit=20` | the recent jobs, newest first |

- `price_indices` lists one entry per series mapped from an imported set's currency: series, label, months, latest month, and the base-year average for the active set.
- A series with no values is listed with `months: 0`.

### Web page and Settings tab

- The route `routes/_authed/settings/emission-factors.tsx` has `staticData.title = 'Emission factors'`. Settings appends its tab to the others only for system admins. For a non-system-admin, it renders a "System admins only" notice instead of calling the API.
- Components live in `components/settings/emission-factors/`, one file each:
  - `factor-sets-table`
  - `activate-dialog`
  - `price-index-card`
  - `workbook-upload`
  - `import-jobs`
  - `coverage-table`
- The jobs query refetches every 2 s while any job is `queued` or `running`. When a job finishes, the page invalidates the status query, and the emissions queries on other pages too, since an activation or a new index changes every figure.
- The upload uses a new `FileDropzone` in the UI library (`components/ui/forms/file-dropzone.tsx`): a dashed drop area that highlights on drag-over, a browse button, `accept` and `maxBytes` checks with a stated reason, and the chosen file's name and size with a remove button. It is controlled (`value`, `onChange`) so any form can use it.

## Risks / Trade-offs

- **[The web API restarts mid-import]** → The job is marked interrupted on startup. The import's single transaction leaves the database unchanged, so the admin just uploads again.
- **[Several web API workers]** → `BackgroundTasks` runs in whichever worker took the request. The "one running job per kind" check is in the database, so a second worker's request still gets `409`. The upload's temp file is local to that worker, and so is its job.
- **[Memory: openpyxl reading a large workbook]** → This is the same cost as the CLI, now inside the API process. The workbook is read in read-only mode, as it is today, and imports are rare and single-flight.
- **[Activating the wrong release changes every figure at once]** → A confirmation names both sets. The action is audited, and switching back is one click.
- **[Admin routes are reachable by URL]** → Every endpoint checks `require_system_admin` on the server. The page's notice is only a courtesy.

## Migration Plan

1. Archive `spend-based-emissions` and `emissions-inflation-adjustment`.
2. The user syncs dependencies (`python-multipart` declared) and runs migration `0019`.
3. Deploy. The Emission factors tab appears in Settings for system admins.

To roll back, hide the tab; the tables and endpoints are additive.

## Open Questions

None blocking. Deleting old factor sets can follow once there is more than one release to clean up.
