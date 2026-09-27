## ADDED Requirements

### Requirement: The sidebar SHALL end with system-admin entries for system admins

The app shell's sidebar SHALL end with a footer at the bottom left, rendered only for system admins, headed "System". It SHALL list the system-admin pages as router links styled like the main navigation, with the same active marking. Its first entry SHALL be **Emission factors**, linking to `/admin/emission-factors`.

For anyone who is not a system admin, the footer SHALL NOT be rendered.

#### Scenario: A system admin sees the admin entries

- **WHEN** a system admin is signed in
- **THEN** the bottom of the sidebar shows "System" with an Emission factors entry, marked active on `/admin/emission-factors`

#### Scenario: Others don't

- **WHEN** an organization admin who is not a system admin is signed in
- **THEN** the sidebar has no System footer
