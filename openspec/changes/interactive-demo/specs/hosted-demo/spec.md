## ADDED Requirements

### Requirement: The demo serves only fictional data behind one shared login

The hosted demo SHALL serve only the fictional Nordlys Byg A/S, loaded from
`apps/demo/postgres/demo.sql.gz`, and never customer or development data.
Visitors SHALL sign in with one shared login. That login SHALL be a Member of
the demo's Clerk organization, so Clerk itself lets it manage neither members
nor the organization profile. Its public metadata SHALL mark it as the demo
login, and the session token SHALL carry that mark as the `demo` claim.

#### Scenario: The demo claim sets the role

- **WHEN** a member's token carries `demo: true`
- **THEN** the web API treats the caller as the `demo` role, and without the
  claim as a member

### Requirement: The demo role SHALL see what an organization admin sees

The web API SHALL give a caller whose token has a truthy `demo` claim (the
claim name is `CLERK_DEMO_CLAIM`) the application role `demo`, whatever its
organization role. That role SHALL pass the management and organization-admin
checks for reading, and SHALL NOT pass system-admin checks.

The web app SHALL show a `demo` principal every control it shows an
organization admin, and SHALL NOT show system-admin tools.

#### Scenario: Admin controls are shown

- **WHEN** a visitor signed in with the demo login opens an alternative item,
  the agreements list and Settings → Companies
- **THEN** Find alternatives, the specification editor, Upload agreement, Add
  company and Edit company are shown, as they are for an organization admin

#### Scenario: Admin reads succeed

- **WHEN** the demo login requests the organization, the companies, the spend
  trees and the emission factor status
- **THEN** each response is 200

### Requirement: The demo role SHALL save nothing

The web API SHALL refuse every request from the `demo` role whose method is not
`GET`, `HEAD` or `OPTIONS`. It SHALL respond `403` with the detail "This is a
demo, so changes aren't saved." and change nothing. The refusal SHALL apply to
every authenticated route, including routes added later, without per-route
code.

When the web API refuses a change this way, the web app SHALL show a toast
saying changes aren't saved in the demo. It SHALL keep the dialog or form open
with the visitor's input.

For a `demo` principal, the web app SHALL NOT call Clerk for these actions.
Instead it SHALL show the same message:

- profile name or photo changes;
- adding or removing email addresses;
- password changes;
- session revocation;
- connected-account changes;
- member invitations, role changes and removals;
- organization logo changes.

Every other role SHALL behave as before.

#### Scenario: Every write route refuses the demo login

- **WHEN** the test suite sends each authenticated write route a request from
  the demo login
- **THEN** each response is 403 with "This is a demo, so changes aren't saved."

#### Scenario: Recategorizing in the demo

- **WHEN** a visitor changes a spend line's category and saves
- **THEN** a toast says changes aren't saved in the demo, the editor stays open
  with the chosen category, and the line keeps its original category

#### Scenario: Changing the shared password

- **WHEN** a visitor submits the password form on the Profile page
- **THEN** Clerk is not called, and a toast says changes aren't saved in the demo

#### Scenario: Other roles are unaffected

- **WHEN** a moderator creates a spend tree
- **THEN** it is saved as before

### Requirement: The demo SHALL say it is a demo

For a `demo` principal, every page of the web app SHALL show a banner. It SHALL
say that this is the Heftra demo, that the visitor can try anything, and that
changes aren't saved. Other principals SHALL see no banner.

#### Scenario: The banner

- **WHEN** a visitor signs in with the demo login
- **THEN** each page shows the demo banner, and an organization admin's pages
  don't

### Requirement: The demo SHALL reset to its original data every night

The demo stack SHALL restore the original demo data every day at 03:00
Europe/Copenhagen, and on demand with `docker compose run --rm reset reset-now`.

A reset SHALL:

- load the dump into a separate database before touching the live one;
- link the organization to the configured Clerk organization;
- keep the stand-in ERP's registered credentials, so invoice PDFs keep working
  without a restart;
- replace the live database in one swap.

A reset SHALL leave the live database untouched if the load fails, or if the
dump's schema revision differs from the live database's.

#### Scenario: Edits are gone the next morning

- **WHEN** the data was changed (for example by hand) and the nightly reset runs
- **THEN** the data is back to the dump's, and the dashboard and
  invoice PDFs work

#### Scenario: A stale dump is refused

- **WHEN** the dump's `alembic_version` differs from the live database's
- **THEN** the reset logs the mismatch, discards the loaded copy, and the live
  database is unchanged
