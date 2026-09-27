## ADDED Requirements

### Requirement: The dashboard's emissions SHALL say whether they are adjusted for inflation

The dashboard's emissions section SHALL follow its method line with "adjusted with <index label>" when the report's factor set carries a price index, and with "not adjusted for inflation" when it does not.

#### Scenario: Adjusted

- **WHEN** the report's factor set carries US CPI
- **THEN** the section's method line says "adjusted with US CPI"

#### Scenario: Not adjusted

- **WHEN** the report's factor set has no price index
- **THEN** the section's method line says "not adjusted for inflation"
