## Why

Emission factors and the price index are global reference data. Today the only way to manage them is two CLIs on the server: `import_factors` for an Open CEDA workbook, and `import_series` for US CPI. There is no way from the app to see:
- which factor set is active;
- when the index was last refreshed;
- how much of each company's spend has an emission sector.

A system admin who wants to load next year's workbook, switch releases or refresh CPI needs shell access. This change adds those controls to the app for system admins, in a new admin area at the bottom of the sidebar.

## What Changes

- **Admin API** (system admins only, `/api/v1/admin/emission-factors/...`):
  - **Status:** every factor set (source, version, classification, price year, sector and factor counts, imported, active); the price index each set's currency uses (series, latest month, number of months); and, per company, how many invoice lines have an AI sector, a human sector, a sector needing review, or none.
  - **Activate** an imported factor set. It becomes the only active one, and the change is audited.
  - **Refresh the price index** from FRED, as the CLI does.
  - **Upload an Open CEDA workbook** (`.xlsx`, at most 50 MB). It is imported in the background, optionally activated once done.
  - **Import jobs:** a stored record of each upload or refresh (kind, file, status, counts or error, who asked, when). This lets the page show progress and history. Jobs run in the web API process; any left running by a restart are marked as interrupted.
- **Web**:
  - A system-admin **Emission factors** page at `/admin/emission-factors`, with:
    - the factor sets, and an activate action with a confirmation;
    - the price index card, with a refresh button;
    - the upload form, with an "activate when imported" choice;
    - the recent jobs, polled while one is running;
    - the per-company coverage, with a **Match emission sectors** action that requests the existing `match_emissions` run.
  - A **sidebar footer** at the bottom left, shown only to system admins, with a **System** label and the **Emission factors** entry. Future admin pages go there too.

## Capabilities

### New Capabilities
- `emission-factor-admin`: the system-admin API for factor sets, the price index, workbook upload, import jobs and matching coverage.
- `frontend-emission-factor-admin`: the Emission factors admin page.

### Modified Capabilities
- `frontend-auth-dashboard`: the app shell's sidebar gains a footer with system-admin entries, hidden from everyone else.

## Impact

- **Order:** this change reuses `emission-factors`, `spend-emissions` and `price-indices` from the two open changes (`spend-based-emissions`, `emissions-inflation-adjustment`). Archive those first.
- **web-api**:
  - New:
    - model and migration `0019_reference_data_imports`;
    - router `routers/admin_emission_factors.py`;
    - a `web_api/reference_imports/` package for job records, running jobs and the upload's temporary file;
    - schemas under `schemas/admin/`.
  - Reuses `read_workbook`/`import_workbook`, `parse_series_csv`/`replace_series` and `require_system_admin`.
  - Needs `python-multipart` for uploads. It is already in `uv.lock` through another package, but web-api must declare it, and the user runs the sync.
- **web**:
  - a new route `routes/_authed/admin/emission-factors.tsx`;
  - components under `components/admin/emission-factors/`;
  - API types and queries;
  - `app-shell.tsx` gains the sidebar footer.
- **Out of scope:**
  - deleting factor sets;
  - editing individual factors or sectors;
  - other factor sources (EXIOBASE);
  - scheduled CPI refresh;
  - the phone-width sidebar.
