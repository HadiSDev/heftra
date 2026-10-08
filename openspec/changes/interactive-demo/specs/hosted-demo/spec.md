## ADDED Requirements

### Requirement: The demo serves only fictional data behind one shared login

The hosted demo SHALL serve only the fictional Nordlys Byg A/S, loaded from
`apps/demo/postgres/demo.sql.gz`, and never customer or development data.
Visitors SHALL sign in with one shared login. That login SHALL be a Member of
the demo's Clerk organization, so Clerk itself lets it manage neither members
nor the organization profile. Its public metadata SHALL mark it as the demo
login, and the session token SHALL carry that mark as the `demo` claim.

#### Scenario: A visitor can manage but not administer

- **WHEN** a visitor signs in with the demo login
- **THEN** management actions on lines, spend trees, agreements and
  alternatives are available, and the organization's danger zone, profile
  editing and member management are not

### Requirement: Database-only actions SHALL work in the demo

In the demo, a visitor SHALL be able to:

- recategorize, verify and edit spend lines, add and delete lines, and choose
  emission sectors;
- edit and verify invoice headers;
- create, edit, import, archive and delete spend trees and their nodes, and
  review spend tree suggestions;
- edit agreement headers and terms, and review agreement findings;
- review alternatives (dismiss, mark as switched, reopen);
- turn ERP accounts on and off;
- read the emission factor sets, price indices and their companies' coverage.

#### Scenario: Recategorizing a line

- **WHEN** a visitor changes a spend line's category in the demo
- **THEN** the change is saved, and the line shows the new category as chosen
  by a person

#### Scenario: Building a spend tree

- **WHEN** a visitor creates a spend tree and adds nodes to it
- **THEN** the tree and its nodes are saved and listed under Spend trees

### Requirement: The demo role SHALL be refused what the demo cannot serve

The web API SHALL give a caller whose token has a truthy `demo` claim (the
claim name is `CLERK_DEMO_CLAIM`) the application role `demo`, whatever its
organization role. That role SHALL pass the management checks that admins and
moderators pass, and SHALL NOT pass organization-admin or system-admin checks.

The web API SHALL refuse a `demo` caller these actions with `403` and the
detail "Not available in the demo":

- **actions that need the worker, an LLM or search**: re-reading an invoice
  document, correcting an alternative's specification, finding alternatives,
  reading an agreement again, analysing agreements, recategorizing failed
  lines, and requesting pipeline runs;
- **actions that need the file store or the real ERP**: uploading an agreement,
  opening an agreement's PDF, testing the ERP connection, refreshing ERP
  accounts, and recomputing FX;
- **actions that would change the shared demo for everyone**:
  - creating, updating, deactivating, activating or deleting a company;
  - connecting, changing, replacing, disconnecting or reconnecting the ERP;
  - deleting an agreement.

For a `demo` principal, the web app SHALL NOT show controls for these actions.
It SHALL also not show the profile's name and email editing or the security
panel's password and session controls.

Every other role SHALL behave as before.

#### Scenario: A hand-made request is refused

- **WHEN** a caller with the demo role posts to find alternatives for an item
- **THEN** the response is 403 "Not available in the demo", and no run is
  queued

#### Scenario: The control is not shown

- **WHEN** a principal with the demo role opens an alternative item
- **THEN** the review actions are shown, and Find alternatives and the
  specification editor are not

#### Scenario: The demo claim sets the role

- **WHEN** a member's token carries `demo: true`
- **THEN** the web API treats the caller as the demo role, and without the claim
  as a member

#### Scenario: Other roles are unaffected

- **WHEN** a moderator requests to find alternatives for an item
- **THEN** the request is accepted as before

#### Scenario: The demo role cannot administer the organization

- **WHEN** a caller with the demo role updates the organization profile
- **THEN** the response is 403

#### Scenario: Every write route is classified

- **WHEN** the test suite lists every mutating web API route
- **THEN** each one is either refused to the demo role or named on the demo's
  allow-list, so a new route forces a decision

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

- **WHEN** a visitor recategorizes a line and the nightly reset runs
- **THEN** the line has its original category again, and the dashboard and
  invoice PDFs work

#### Scenario: A stale dump is refused

- **WHEN** the dump's `alembic_version` differs from the live database's
- **THEN** the reset logs the mismatch, discards the loaded copy, and the live
  database is unchanged
