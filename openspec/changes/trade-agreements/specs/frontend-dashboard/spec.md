## ADDED Requirements

### Requirement: The dashboard SHALL show the period's contract rule breaks

When the chosen company has an active agreement, the dashboard SHALL have a contract compliance section for the period, showing:
- the count and amount of open rule breaks;
- the off-contract spend and the overcharges;
- the suppliers bought from off-contract, most first;
- a link to Agreements.

With no active agreement, it SHALL invite the user to upload one. It SHALL load, fail and hold its place like the dashboard's other sections.

#### Scenario: Rule breaks this quarter

- **WHEN** the quarter has four open rule breaks totalling DKK 38,000, mostly with Proshop
- **THEN** the section shows 4 rule breaks, DKK 38,000, and Proshop first among the suppliers

#### Scenario: No agreements yet

- **WHEN** the company has no active agreement
- **THEN** the section says no agreements are uploaded and links to Agreements
