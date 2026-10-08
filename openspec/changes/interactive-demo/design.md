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

The owner wants visitors to see every option an organization admin has, and
to save nothing.

## Goals / Non-Goals

**Goals:**

- A visitor sees every control an organization admin sees, and can walk
  through every dialog.
- Nothing a visitor does is saved, and they are told so clearly, at the moment
  they try.
- A new write route is covered without anyone remembering to add a guard.
- Every role other than `demo` behaves exactly as before.
- Emission factor sources can be shown to customers, not just system admins.

**Non-Goals:**

- Running AI, the worker or a file store in the demo.
- Pretending a save worked (optimistic updates that vanish on reload).
- Showing system-admin tools to visitors.

## Decisions

### 1. The demo login is marked by a session claim and gets the `demo` role

Custom Clerk organization roles need a paid Clerk plan, so the demo login is
marked the way system admins already are:

- its public metadata gets `demo: true`;
- the production session token gains the claim
  `"demo": "{{user.public_metadata.demo}}"` next to `system_admin`.

In Clerk the user stays an org **member**, so Clerk's own frontend API lets it
neither invite, remove or re-role members nor edit the organization profile.

`principal_from_claims` gives a caller with a truthy `demo` claim
(`CLERK_DEMO_CLAIM`) the role `demo`, whatever its org role. Code that doesn't
know the claim (an older deploy) ignores it, so the user stays a read-only
member. That means the claim can be set before or after a deploy.

*Alternative*: a custom Clerk role, `org:demo`. Rejected because it needs a
paid plan.

*Alternative*: make the user `org:admin`. Rejected because admins really can
write: suspending the organization, managing the production org's members.

### 2. See like an admin: the demo role passes the read-side gates

- **Web API**: `require_management` and `require_org_admin` accept `demo`, so
  every read an organization admin can make, the demo login can make. System
  admin checks don't accept it.
- **Web app**: `canManageCompanies` and `canManageOrganization` are true for
  the demo role, so every admin control renders. `principal.demo` is true for
  it, and drives the banner and the Clerk guard.

### 3. Save nothing: one refusal at the root

`current_user` is the dependency behind every authenticated route.
`tenant_scope` builds on it, and the few routes without a tenant use it
directly. When the caller's role is `demo` and the request method isn't `GET`,
`HEAD` or `OPTIONS`, it raises `403` with the detail "This is a demo, so
changes aren't saved."

Because the refusal sits at the root:

- route bodies and decorators don't change;
- a write route added later is refused without anyone touching it. A test walks
  every write route in every router and asserts the refusal, so a route that
  slips past `current_user` fails it.

The web app recognises the refusal in one place: an `ApiError` with status 403
and that detail. A global `MutationCache` error handler shows a toast, "Changes
aren't saved in the demo". The mutation has failed, so dialogs stay open with
the visitor's input, and inline error text shows the same sentence.

Clerk-direct actions (profile name and photo, emails, password, sessions,
connected accounts, member invites and roles, organization logo) never reach
the web API. For the demo principal, a guard in the web app intercepts their
handlers and shows the same toast instead of calling Clerk. A visitor using
Clerk's API by hand could still change the shared login. The README keeps the
"watch the demo user" advice, and the nightly reset doesn't cover Clerk.

The agreement document pane keeps a "not available in the demo" note. The
demo has no file store, so the PDF request could only fail; that's a read, not
an option to show.

*Alternative*: refuse per route with a decorator dependency (the first
version). Rejected because every new write route needs remembering, and an
allow-list stops making sense when nothing is allowed.

### 4. A banner sets expectations

`principal.demo` renders a slim, neutral banner at the top of the app shell:
"You're exploring the Heftra demo. Try anything — changes aren't saved, and the
demo resets every night." It uses ink and neutral tokens only, and a status
role that isn't re-announced.

### 5. Nightly reset: a safety net, restore beside, then swap

Nothing a visitor does should change the data, but the reset restores it every
night in case something slips through (a future route, a manual change). A
`reset` service is built from `apps/demo/postgres/`, so it has `psql`,
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

### 6. Emission factors: read for everyone, scoped coverage

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
  intercepts the controls, and the README tells the owner how to reset it.
  Clerk can't make one user's password immutable.
- **[A visitor expects a save to stick]** → The toast, the inline error and the
  banner all say changes aren't saved.
- **[A route reaches the database without `current_user`]** → The write-route
  test fails for it. Unauthenticated routes (public demo requests, Clerk
  webhooks) are named in the test and are not tied to the demo login.
- **[The dump falls behind a migration]** → The reset refuses to swap, and logs
  why. The existing README rule (rebuild the dump after schema changes)
  applies.
- **[The session token changes in production Clerk]** → It gains one claim,
  read from public metadata, which only the backend can set. Only the demo user
  has it set.

## Migration Plan

1. Merge the code. No role but `demo` changes behaviour.
2. Add the `demo` session claim in production Clerk, and set
   `public_metadata.demo` on `demo@heftra.com`. Until the redeploy, the deployed
   code ignores the claim, so the demo stays read-only.
3. Hadi redeploys the demo on Dokploy. The `demo_pgdata` volume can stay.
4. Check on `demo.heftra.com`, then run `reset-now` once to confirm the reset.

**Rollback**: remove `demo` from the user's public metadata. The demo login is
then a plain member again, which sees no admin controls.
