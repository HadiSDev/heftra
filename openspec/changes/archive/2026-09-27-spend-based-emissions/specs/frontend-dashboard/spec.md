## ADDED Requirements

### Requirement: The dashboard SHALL show the period's estimated emissions

The dashboard SHALL have an emissions section for the chosen period and company, showing:
- the period's estimated kg CO₂e, in tonnes from 1,000 kg, and its change from the comparison period;
- the twelve months ending with the period, as a small chart;
- the share of posted spend that has an estimate;
- the five sectors with the most emissions;
- the method line and the factor set's attribution;
- a link to Spend Lines for the same period.

With no active factor set it SHALL say that no emission factors are imported. It SHALL load, fail and hold its place like the dashboard's other sections.

#### Scenario: The period's emissions

- **WHEN** the dashboard shows a quarter whose vouchers are estimated at 2.4 t CO₂e, up from 2.0 t
- **THEN** the emissions section shows 2.4 t CO₂e with a 20% rise, the months, the share estimated and the top sectors

#### Scenario: No factors

- **WHEN** no factor set is active
- **THEN** the emissions section says no emission factors are imported
