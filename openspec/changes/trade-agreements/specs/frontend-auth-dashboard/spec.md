## ADDED Requirements

### Requirement: The navigation SHALL offer Agreements

The sidebar navigation SHALL offer an **Agreements** entry after Suppliers, linking to `/agreements`, marked active on that page and its detail pages.

#### Scenario: Opening Agreements

- **WHEN** a signed-in user activates the Agreements entry
- **THEN** the router navigates to `/agreements` and the entry is marked active
