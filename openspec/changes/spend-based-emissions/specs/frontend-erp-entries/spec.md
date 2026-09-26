## ADDED Requirements

### Requirement: Spend Lines SHALL show the estimated emissions of what it lists

Beside the coverage card, Spend Lines SHALL show an emissions card fed by the emissions summary under the page's current filters. The card SHALL show:
- the total estimated emissions;
- the share of posted spend that was estimated, per base currency;
- a method line naming the factor set, its version and its price year and currency (for example "Spend-based estimate · Open CEDA 2025 · 2022 USD");
- the factor set's attribution;
- the number of vouchers not estimated, broken down by reason on hover or focus.

Totals SHALL be shown in kg CO₂e below 1,000 kg and in t CO₂e with one decimal from 1,000 kg. With no active factor set, the card SHALL say that no emission factors are imported and show no figure. The card SHALL load, fail and retry independently of the coverage card, and SHALL keep its size while loading so the page does not shift.

#### Scenario: The card follows the filters

- **WHEN** a user filters Spend Lines to one supplier
- **THEN** the emissions card shows that supplier's estimated emissions and share of spend estimated

#### Scenario: Large totals are shown in tonnes

- **WHEN** the filtered vouchers are estimated at 12,437 kg CO₂e
- **THEN** the card shows 12.4 t CO₂e

#### Scenario: No factors imported

- **WHEN** no factor set is active
- **THEN** the card says no emission factors are imported, with no figure

#### Scenario: The attribution is shown

- **WHEN** the card shows a figure from Open CEDA
- **THEN** "CEDA by Watershed" is visible on the card

### Requirement: Each voucher and line SHALL show its estimated emissions

The voucher table SHALL have a CO₂e column showing each voucher's estimated emissions.
- A `partial` voucher SHALL be marked as partly estimated.
- A voucher with nothing estimated SHALL show "—", with its reason available on hover and focus.

Each expanded line SHALL show:
- its emissions;
- its emission sector's name;
- a mark distinguishing an AI match from a human choice;
- for an AI match below the review threshold, a needs-review mark like a low-confidence category.

The country whose factor was used SHALL be available on hover and focus.

#### Scenario: A voucher row shows its emissions

- **WHEN** an estimated voucher is listed
- **THEN** its row shows its CO₂e in the CO₂e column

#### Scenario: A voucher with no lines

- **WHEN** a journal-only voucher is listed
- **THEN** its CO₂e shows "—" and its reason says it has no invoice lines

#### Scenario: A line shows its sector and emissions

- **WHEN** a voucher with a matched line is expanded
- **THEN** the line shows its sector's name, whether it was matched by AI or chosen by a human, and its CO₂e

### Requirement: A line's emission sector SHALL be chosen from the active sectors

The line editor SHALL offer an emission sector picker that:
- searches the active factor set's sectors as the user types;
- shows each sector's name and code;
- saves the choice through the line update, then refreshes the voucher list and the emissions card.

The picker SHALL offer to clear the sector. It SHALL be disabled, with an explanation, when no factor set is active.

#### Scenario: A reviewer corrects a sector

- **WHEN** a reviewer searches for "freight", picks a sector and saves
- **THEN** the line shows that sector as a human choice, and the voucher's CO₂e and the emissions card update

#### Scenario: No factors imported

- **WHEN** no factor set is active and a reviewer opens a line
- **THEN** the sector picker is disabled and says no emission factors are imported
