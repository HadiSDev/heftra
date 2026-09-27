## MODIFIED Requirements

### Requirement: A line's emissions SHALL show how they were reached

A line's CO₂e in the voucher table SHALL reveal on hover and focus the calculation behind it:
- its spend;
- the conversion to the factor's currency;
- when adjusted, the deflation to the factor's price year, naming the index and the month used;
- the factor and the country or region it is for;
- the result.

The line editor in the voucher panel SHALL show an emissions section with:
- the sector, and whether AI matched it or a person chose it;
- for an AI match, its confidence and its reasoning;
- the calculation, step by step: the line's share of the voucher's spend, the rate and converted amount, the deflation when adjusted, the factor with its sector and area, and the kg CO₂e.

For a line with no estimate it SHALL say why.

#### Scenario: A reviewer sees how a line's emissions were reached

- **WHEN** a reviewer opens a line estimated at 65.9 kg CO₂e
- **THEN** the panel shows DKK 1,000.00 × 0.145 = USD 145.00, × US CPI 2023 average 300 ÷ Aug 2026 330 = USD 131.82 in 2023 dollars, × 0.5 kg CO₂e per USD (factor for DE) = 65.9 kg CO₂e, and the AI's reasoning for the sector

#### Scenario: An unadjusted line has no deflation step

- **WHEN** a reviewer opens a line whose calculation has no deflation
- **THEN** the calculation goes straight from the converted amount to the factor

## ADDED Requirements

### Requirement: The emissions card SHALL say whether figures are adjusted for inflation

The emissions card's method line SHALL end with "adjusted with <index label>" when the factor set carries a price index, and with "not adjusted for inflation" when it does not. The latest month of the index SHALL be available on hover and focus.

#### Scenario: Adjusted

- **WHEN** the factor set's price index is US CPI through August 2026
- **THEN** the method line reads "Spend-based estimate · CEDA 2025 · 2023 USD · adjusted with US CPI", and hovering it shows that the index runs to August 2026

#### Scenario: Not adjusted

- **WHEN** the factor set has no price index
- **THEN** the method line ends with "not adjusted for inflation"
