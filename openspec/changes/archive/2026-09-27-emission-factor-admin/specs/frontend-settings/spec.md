## ADDED Requirements

### Requirement: System admins SHALL find Emission factors as a Settings tab

Settings SHALL show an **Emission factors** tab after its other tabs, linking to `/settings/emission-factors`, only for system admins. For anyone else the tab SHALL NOT be rendered. The sidebar SHALL NOT gain an entry for it.

#### Scenario: A system admin sees the tab

- **WHEN** a system admin opens Settings
- **THEN** the last tab is Emission factors

#### Scenario: Others don't

- **WHEN** an organization admin who is not a system admin opens Settings
- **THEN** there is no Emission factors tab
