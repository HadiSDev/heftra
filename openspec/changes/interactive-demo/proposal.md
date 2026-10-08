## Why

The hosted investor demo at `demo.heftra.com` shows only half the product. Its
shared login is a Clerk org **member**, and every management control is hidden
from members. So a visitor never sees how lines are recategorized, how a spend
tree is built, how agreements and alternatives are reviewed, or how a company
and its ERP are set up. The emission factor sources behind every emissions
figure are visible to system admins only, so they can't be shown at all.

The owner wants visitors to **see every option an organization admin has, but
save nothing**. The demo data stays exactly as it was built, and nothing a
visitor clicks can break it for the next one.

## What Changes

- **A `demo` role for the shared login.**
  - The demo user stays an org **member** in Clerk, so Clerk itself lets it
    manage neither members nor the organization profile.
  - Its public metadata gets `demo: true`. A `demo` session claim carries that
    mark, the same way the existing `system_admin` claim works. (Custom Clerk
    organization roles need a paid plan.)
  - The web API gives a caller with the claim the application role `demo`.
- **The demo role sees what an organization admin sees.** It passes the
  management and organization-admin checks, so the web app shows every control
  an admin gets:
  - line, invoice and spend tree editing;
  - agreements: upload, terms, findings;
  - alternatives: finding them, specifications, review;
  - companies and their ERP connection, accounts;
  - organization profile and members.

  System-admin tools stay hidden.
- **The demo role saves nothing.**
  - The web API refuses every non-read request from it, in one place (the
    dependency every authenticated route uses), with `403`: "This is a demo, so
    changes aren't saved."
  - The web app shows that as a toast and leaves the dialog open with the
    visitor's input.
  - Profile, password, email and member changes go straight to Clerk, so the
    web app intercepts them for the demo login with the same message.
- **A demo banner.** Every page carries a slim banner telling visitors they're
  in the demo, that they can try anything, and that changes aren't saved.
- **A nightly reset as a safety net.** A `reset` service in the demo stack
  restores the original Nordlys Byg data at 03:00 Europe/Copenhagen. It keeps
  the stand-in ERP's credentials, and refuses a dump whose schema is behind.
- **Emission factors become readable by every user.**
  - `GET /api/v1/admin/emission-factors` is open to any signed-in user, with
    coverage scoped to the caller's own companies unless they are a system
    admin.
  - Writes and the import history stay system-admin only.
  - Settings shows everyone else a read-only page.

## Capabilities

### New Capabilities

- `hosted-demo`: the investor demo covers:
  - its data and shared login;
  - the `demo` role (see like an admin, save nothing);
  - the demo banner and the refusal message;
  - the nightly reset.

### Modified Capabilities

- `emission-factor-admin`: the status endpoint is readable by every signed-in
  user, with coverage scoped to their organization. Writes and import history
  stay system-admin only.
- `frontend-emission-factor-admin`: everyone who isn't a system admin sees a
  read-only Emission factors page instead of a "System admins only" notice.

## Impact

- **`apps/web-api`**:
  - `auth/principal.py`: the `demo` claim (`CLERK_DEMO_CLAIM`) and role;
  - `auth/deps.py`: `current_user` refuses the demo role's writes; the
    management and organization-admin checks accept it;
  - emission factor status gating and coverage scoping;
  - tests that walk every write route.
- **`apps/web`**:
  - the demo role in the role gates;
  - one detector for the demo refusal, and a global mutation error toast;
  - a guard on Clerk-direct actions;
  - the demo banner;
  - the read-only emission factors page;
  - tests.
- **`apps/demo`**: a `reset` service and script (`link-org` reuses it), and the
  README.
- **Clerk (production, done)**: the `demo` session claim, and
  `public_metadata.demo` on `demo@heftra.com`.
- **Deploy**: Hadi redeploys the demo on Dokploy. The dump is unchanged, so the
  `demo_pgdata` volume can stay.
