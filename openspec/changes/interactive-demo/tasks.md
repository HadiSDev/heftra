## 1. Preflight

- [x] 1.1 Re-read `git status`, and stop if another agent has uncommitted edits in the files below. Record baselines: `uv run pytest -q apps/web-api`, the `apps/web` vitest count, and `tsc --noEmit`.

## 2. Web API demo mode

- [x] 2.1 Add the application role `demo` (`auth/principal.py`), accept it in `require_management`, and add a `refuse_in_demo` dependency in `auth/deps.py` that raises 403 "Not available in the demo" for that role.
- [x] 2.2 Add `refuse_in_demo` to the route decorators listed in design Decision 3:
  - `invoices.py`: retrigger;
  - `alternatives.py`: specification, find alternatives for an item and for a line;
  - `agreements.py`: upload, file download, delete, read again, analyse;
  - `companies.py`: create, update, recompute FX, recategorize failed lines, deactivate, activate, delete;
  - `erp_integrations.py`: connect, patch, replace, disconnect, reconnect, test, refresh accounts;
  - `pipeline_runs.py`: request a run.
- [x] 2.3 Tests:
  - each group is refused to the demo role and not to a moderator;
  - the demo role can choose an emission sector and build a spend tree, and can't manage the organization;
  - a route inventory test classifies every mutating route as refused or allow-listed.

## 3. Emission factors readable by everyone

- [x] 3.1 `admin_emission_factors.py`: drop the router-wide `require_system_admin`. Gate each write route and `GET /imports` with `require_system_admin`, and `GET ""` with `tenant_scope`.
- [x] 3.2 `coverage_rows(session, company_ids)`: filter to the given companies; the status passes `None` for system admins and `scope.company_ids` otherwise.
- [x] 3.3 Tests:
  - a member gets 200 with only their organization's coverage;
  - a system admin sees every company;
  - writes and `/imports` stay 403 for an organization admin.

## 4. Web app

- [x] 4.1 `demo` on the principal when the role is `demo` (`lib/auth/auth.tsx`), and the demo role in `canManageCompanies`.
- [x] 4.2 Hide each refused action's control when `principal.demo`:
  - re-read document;
  - find alternatives (item and line);
  - specification editor;
  - agreement upload, PDF link, delete, read again, analyse;
  - company create, edit, run menu, recompute FX, recategorize failed, deactivate/activate, delete;
  - ERP connect, change, replace, disconnect, reconnect, test, refresh accounts.
- [x] 4.3 Hide the profile's name and email editing and the security panel's password and session controls when `principal.demo`.
- [x] 4.4 Emission factors route:
  - render the page for everyone, with `readOnly` for non-system-admins;
  - in read-only mode, don't fetch import jobs or mount the activate dialog;
  - in read-only mode, the cards hide activate, refresh, upload, jobs and match controls;
  - show the Settings nav entry to everyone.
- [x] 4.5 Tests:
  - the demo role hides the refused controls and keeps the database-only ones (line editor, tree editor, alternative review);
  - the emission factors page renders read-only for a member without requesting `/imports`;
  - existing tests pass with demo mode off.

## 5. Demo stack

- [x] 5.1 `apps/demo/postgres/reset.sh` per design Decision 4:
  - load the dump into `heftra_next`;
  - link the org;
  - copy the `erp_credentials` rows;
  - check that the alembic versions match;
  - swap the databases and drop the old one;
  - a `reset-now` mode, plus a daily 03:00 Europe/Copenhagen loop.

  The `postgres` Dockerfile copies the script in.
- [x] 5.2 `docker-compose.yml`:
  - a `reset` service built from `./postgres`, with `TZ=Europe/Copenhagen`, the DB password and `DEMO_CLERK_ORG_ID`, after `link-org` (which now runs the same script).
- [x] 5.3 Test the reset against a local copy of the stack, built from the real dump (postgres plus `reset` only):
  - recategorize a row, run `reset-now`, and check the row is restored;
  - check `erp_credentials` survives;
  - check the org link is set;
  - check a mismatched `alembic_version` keeps the live database.
- [x] 5.4 README: what visitors can and can't do, demo mode, the reset (schedule, `reset-now`, the stale-dump refusal), and the demo role setup replacing the Member step.

## 6. Clerk

- [x] 6.1 Show the owner the exact Clerk CLI commands:
  - add the session claim `"demo": "{{user.public_metadata.demo}}"` to the production session token;
  - set `public_metadata.demo = true` on `demo@heftra.com`.

  Custom org roles need a paid plan, so the role comes from this claim instead. Run the commands only after the owner confirms, then verify both.

## 7. Verify and land

- [x] 7.1 Full `uv run pytest -q`, the web vitest suite and `tsc --noEmit` pass at the baseline plus the new tests. `openspec validate interactive-demo --strict` passes.
- [x] 7.2 Commit on `main`, and hand Hadi the redeploy steps (no volume removal needed).
