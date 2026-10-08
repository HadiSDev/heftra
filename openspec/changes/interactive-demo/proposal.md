## Why

The hosted investor demo at `demo.heftra.com` is read-only. Its shared login is
a Clerk org **member**, and every write needs admin or moderator, so a visitor
can look at categorized lines but can never do anything: no recategorizing, no
spend tree editing, no reviewing alternatives or agreement findings. Investors
only see half the product. The emission factor sources behind every emissions
figure are visible to system admins only, so they can't be shown at all.

The demo runs no AI, worker or file store. That should stay true. Most of what
a user does in the product is a database write, which the demo can already
serve.

## What Changes

- **A new role, `demo`, more restrictive than moderator.** The shared demo user
  stays an org **member** in Clerk, so Clerk itself lets it manage neither
  members nor the organization profile. Its public metadata gets
  `demo: true`, which a `demo` session claim carries, in the same way as the
  existing `system_admin` claim. (Custom Clerk organization roles need a paid
  Clerk plan.) The web API gives a caller with that claim the application
  role `demo`, which passes the management checks for database-only writes, so
  visitors can:
  - recategorize, verify and edit spend lines, and choose emission sectors;
  - edit and verify invoice headers;
  - create, edit, import, archive and delete spend trees;
  - edit agreement terms and review agreement findings;
  - review alternatives (dismiss, switched, reopen);
  - turn ERP accounts on and off.
- **The demo role is refused what the demo can't serve.** The web API refuses
  it (`403`, "Not available in the demo") and the web app hides the controls
  for actions in three groups:
    - **would wait forever on the worker or AI**: re-reading a document,
      finding alternatives, editing a specification, reading or analysing
      agreements, pipeline runs, recategorizing failed lines;
    - **need the file store or a real ERP**: uploading an agreement, opening its
      PDF, refreshing accounts, testing the connection, recomputing FX;
    - **would break the demo for everyone**: creating, editing, deactivating or
      deleting a company, connecting, changing or disconnecting the ERP,
      deleting an agreement, and changing the shared login's profile, email or
      password.
  - No flag or deploy setting is involved: every other role behaves exactly
    as before, and the demo stays restricted however it is deployed.
- **The demo resets nightly.** A `reset` service in the demo stack restores the
  original Nordlys Byg data at 03:00 Europe/Copenhagen. It re-links the Clerk
  org, and the stand-in ERP re-registers, so invoice PDFs keep working. One
  investor's edits are visible to the next investor only until that night.
- **Emission factors become readable by every user.**
  - `GET /api/v1/admin/emission-factors` is opened to any signed-in user.
    Coverage is scoped to the caller's own companies unless they are a system
    admin.
  - Every write, and the import history, stays system-admin only.
  - The Settings page shows a read-only view to everyone else: factor sets,
    price indices and their own companies' coverage, without activate,
    refresh, upload, jobs or match actions.

## Capabilities

### New Capabilities

- `hosted-demo`: the investor demo stack covers:
  - its data;
  - the shared login's role;
  - demo mode, and which actions it hides and refuses;
  - the nightly reset;
  - the stand-in ERP's re-registration.

### Modified Capabilities

- `emission-factor-admin`: the status endpoint is readable by every signed-in
  user, with coverage scoped to their organization. Writes and import history
  stay system-admin only.
- `frontend-emission-factor-admin`: everyone who isn't a system admin sees a
  read-only Emission factors page instead of a "System admins only" notice.

## Impact

- **`apps/web-api`**:
  - a `demo` application role (`auth/principal.py`), accepted by
    `require_management`;
  - a `refuse_in_demo` dependency on the listed routes (invoices, alternatives,
    agreements, companies, ERP integrations, pipeline runs);
  - `admin_emission_factors.py` per-route gating;
  - `admin/coverage.py` scoping;
  - tests.
- **`apps/web`**:
  - `demo` on the principal when the role is `demo`, and the demo role in
    `canManageCompanies`;
  - the components behind each listed action;
  - the profile and security panels;
  - the emission factors route and its cards gain read-only rendering;
  - tests.
- **`apps/demo`**:
  - `docker-compose.yml`: a `reset` service
    built from `postgres/`;
  - a reset script;
  - `demo-erp` re-registers after a reset;
  - the README.
- **Clerk (production, outward-facing)**: add the `demo` session claim, and set
  `public_metadata.demo` on `demo@heftra.com`. Done through the Clerk CLI after
  the owner has seen the commands.
- **Deploy**: Hadi redeploys the demo on Dokploy. The dump is unchanged, so the
  `demo_pgdata` volume can stay.
