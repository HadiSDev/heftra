## MODIFIED Requirements

### Requirement: Dashboard renders live reporting data

The dashboard SHALL render inside the themed AppShell and display live spend figures from the spend reports (`GET /api/v1/reports/spend-*`), for the period and company chosen on the page, as defined by the `frontend-dashboard` capability: tiles, a monthly trend, breakdowns by category and supplier, and insights, with loading, empty, and error states. Monetary figures SHALL be presented grouped by base currency and never summed across currencies. It SHALL NOT show ledger aggregates that net every account (such as a "net ledger"), posting counts, or entry-type counts.

#### Scenario: Data is shown

- **WHEN** the org has spend in the chosen period and the dashboard loads
- **THEN** the tiles, trend, breakdowns and insights display values from the spend reports, with amounts grouped by base currency

#### Scenario: Loading state

- **WHEN** the reports are in flight
- **THEN** the dashboard shows loading placeholders (skeletons) rather than empty or broken content

#### Scenario: Empty state

- **WHEN** the org has no spend in the chosen period
- **THEN** the dashboard shows an explicit empty state instead of zeros that look like an error

#### Scenario: Currency separation

- **WHEN** spend spans multiple base currencies
- **THEN** totals are shown per currency and are not combined into a single sum
