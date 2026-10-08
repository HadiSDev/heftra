## Context

`apps/demo` serves the fictional Nordlys Byg A/S at `demo.heftra.com`. It runs:

- PostgreSQL, loaded once from `postgres/demo.sql.gz` (a plain, owner-less
  `pg_dump`) on an empty `demo_pgdata` volume;
- `link-org`, which points the demo organization at the Clerk org;
- the web API and the web app;
- `demo-erp`, which writes its own address into `erp_credentials`, encrypted,
  when it starts;
- `cloudflared`.

There is no file store, AI service or worker.

Authorization today:

- `auth/principal.py:map_role` maps the Clerk `org_role` (the part after
  `org:`) to `admin|moderator|member|viewer`, and `clerk_sync` stores it on every
  request.
- `require_management` (admin or moderator) guards almost every write.
- `require_org_admin` guards the organization profile and suspension.
- `require_system_admin` guards pipeline runs, company deletion and emission
  factors.
- The web app mirrors this with `canManageCompanies` (admin or moderator) and
  `canManageOrganization` (admin) in `lib/auth/auth.tsx`.
- The demo user is a member, so it fails all of them.

A survey of every action, and what it needs beyond Postgres, sorted them into
four groups:

- **works on the database alone**;
- **queues work nobody runs**: worker, LLM or search;
- **needs the file store or the real ERP API**;
- **damages the shared demo**.

The proposal lists them.

## Goals / Non-Goals

**Goals:**

- A visitor can do everything that works on the database alone.
- A visitor never meets a spinner that never ends, a 500, or a broken demo
  left by a previous visitor.
- Every role other than `demo` behaves exactly as before.
- The demo returns to its original state every night without anyone acting.
- Emission factor sources can be shown to customers, not just system admins.

**Non-Goals:**

- Running AI, the worker or a file store in the demo.
- Per-visitor sandboxes (an org per visitor). A shared, nightly-reset
  workspace is enough for investor walkthroughs.
- Seeding spend tree suggestions or new data. The dump is unchanged.

## Decisions

### 1. The demo user has its own role, `demo`, more restrictive than moderator

Custom Clerk organization roles need a paid Clerk plan, so the demo login is
marked the way system admins already are. Its public metadata gets
`demo: true`, and the production session token gains the claim
`"demo": "{{user.public_metadata.demo}}"` next to `system_admin`. In Clerk the
user stays an org **member**, so Clerk's own frontend API lets it neither
invite, remove or re-role members nor edit the organization profile.

`principal_from_claims` gives a caller with a truthy `demo` claim
(`CLERK_DEMO_CLAIM`) the role `demo`, whatever its org role. `map_role` knows
`demo` as an application role:

- `require_management` and `canManageCompanies` accept it;
- `require_org_admin` and `canManageOrganization` don't.

So it reaches the database-only writes and nothing above them. Code that
doesn't know the claim (an older deploy) ignores it, and the user stays a
member, which is read-only. So the claim can be set before or after a deploy
without exposing anything.

*Alternative*: a custom Clerk organization role, `org:demo`. Rejected because
it needs a paid Clerk plan. The claim gives the same application role for free.

*Alternative*: make the user `org:admin`. Rejected for two reasons. Admin passes
`require_org_admin`, so a visitor could suspend the organization, and every
request would return 403 until a reset. Clerk would also let a visitor manage
the members of the production org.

*Alternative*: make the user `org:moderator`, and add an env flag on each side
to hide and refuse the demo's missing features. Rejected (the owner asked for a
dedicated role). It also ties the restriction to deploy settings: a demo
deployed without the flags would hand a moderator's shared login actions that
hang or break the demo.

### 2. The role decides, on both sides

- **Web API**: a dependency, `refuse_in_demo`, returns `403` with detail "Not
  available in the demo" when the caller's role is `demo`, and does nothing
  otherwise. It is added to each refused route's decorator `dependencies`, so
  the route bodies don't change.
- **Web app**: `principal.demo` is true when the role is `demo`
  (`lib/auth/auth.tsx`). Components hide each refused action's control with
  `!principal.demo`, next to the existing `canManage` checks.

The UI hides; the API refuses. A stale tab or a hand-made request can't get
past the API, and the UI never shows a control that would only error.

*Alternative*: derive the restriction from `VITE_DEMO_EMAIL` being set.
Rejected because a sign-in convenience shouldn't silently change what the app
allows, and the API would still need its own signal.

### 3. What demo mode refuses

The routes come from the survey. Names are the web API router files.

**Queues work nobody runs:**

- `invoices`: re-read a document (`retrigger`);
- `alternatives`: correct a specification, find alternatives (item and line);
- `agreements`: read again, analyse;
- `companies`: recategorize failed lines;
- `pipeline_runs`: request a run (already system admin only).

**Needs the file store or the real ERP:**

- `agreements`: upload; open the PDF (an S3 read, which already returns 503);
- `erp_integrations`: test connection, refresh accounts;
- `companies`: recompute FX.

**Damages the shared demo:**

- `companies`: create, update (name, spend tree, currency), deactivate,
  activate, delete;
- `erp_integrations`: connect, patch, replace, disconnect, reconnect;
- `agreements`: delete.

Spend tree deletion stays allowed. The API already refuses to delete the tree
a company uses, and the nightly reset restores the rest. ERP account toggles
stay allowed; they only change which accounts a future sync would import.

In the web app, the same actions are hidden in demo mode. So are the Profile
page's name/email editing and the Security panel's password and session
controls. These are Clerk calls the API can't intercept, and the shared
password is printed on the sign-in page. Hiding them doesn't stop a determined
visitor using Clerk's API directly; the README keeps the "watch the demo user"
advice for that.

### 4. Nightly reset: restore beside, then swap

A `reset` service is built from `apps/demo/postgres/`, so it has `psql`,
`pg_dump` and the dump. Its script runs once a day at 03:00 Europe/Copenhagen
(`TZ` set on the service), and can also be run by hand with
`docker compose run --rm reset reset-now`.

Each run:

1. Creates `heftra_next` and loads the dump into it.
2. Links the organization to `DEMO_CLERK_ORG_ID`, as `link-org` does.
3. Copies the live `erp_credentials` rows from `heftra` into `heftra_next`,
   using `pg_dump --data-only -t public.erp_credentials`. The dump has none,
   because `demo-erp` writes them at startup. Copying them keeps invoice PDFs
   working without restarting `demo-erp`.
4. Checks that `alembic_version` in `heftra_next` equals the live database's.
   If it doesn't, the dump is older than the deployed schema: the script logs
   that, drops `heftra_next`, and keeps the live database.
5. Swaps the databases:
   - stop new connections to `heftra` and end its sessions;
   - rename `heftra` → `heftra_previous` and `heftra_next` → `heftra`;
   - drop `heftra_previous`.

   The web API's pool reconnects on its next checkout.

Loading beside the live database keeps downtime to the swap (well under a
second). A failed load never touches the live data.

*Alternative*: drop `demo_pgdata` and restart. Rejected because it needs the
Docker socket inside the stack, or a person.

*Alternative*: truncate and reload tables in place. Rejected because it locks
every table for the length of the load and can half-apply.

### 5. Emission factors: read for everyone, scoped coverage

- `admin_emission_factors.py` drops its router-wide `require_system_admin`.
- `GET ""` takes `tenant_scope`. Every other route keeps
  `require_system_admin`, including `GET /imports`, whose rows name the system
  admins who ran imports.
- `coverage_rows(session, company_ids=None)` filters to the given companies.
  The status call passes `None` for a system admin, and `scope.company_ids`
  otherwise, so nobody sees another organization's companies.
- Factor sets and price indices are shared reference data and stay unfiltered.

In the web app:

- The route renders `EmissionFactorsAdmin` for everyone.
- For a non-system-admin it passes `readOnly`, and doesn't fetch import jobs or
  mount the activate dialog.
- In read-only mode the cards render their data without activate, refresh,
  upload, jobs or match controls.
- The coverage table drops its organization column when every row is from the
  caller's own organization.

## Risks / Trade-offs

- **[A visitor changes the shared password through Clerk's API]** → The UI
  hides the controls, and the README tells the owner how to reset it. Clerk
  can't make one user's password immutable.
- **[Two visitors edit at once and see each other's changes]** → Acceptable for
  investor walkthroughs. The nightly reset bounds it.
- **[The dump falls behind a migration]** → The reset refuses to swap, and logs
  why. The existing README rule (rebuild the dump after schema changes)
  applies.
- **[A new write route is added without `refuse_in_demo`]** → A test lists every
  mutating route and asserts it is either refused in demo mode or on an
  explicit allow-list. A new route then forces a decision.
- **[The session token changes in production Clerk]** → It gains one claim,
  read from public metadata, which only the backend can set. Only the demo user
  has it set. The owner sees the exact CLI commands before they run.

## Migration Plan

1. Merge the code. No role but `demo` changes behaviour.
2. Add the `demo` session claim in production Clerk, and set
   `public_metadata.demo` on `demo@heftra.com`. Until the redeploy, the deployed
   code ignores the claim, so the demo stays read-only.
3. Hadi redeploys the demo on Dokploy. The `demo_pgdata` volume can stay.
4. Check on `demo.heftra.com`, then run `reset-now` once to confirm the reset.

**Rollback**: remove `demo` from the user's public metadata. The demo is then
read-only again.
