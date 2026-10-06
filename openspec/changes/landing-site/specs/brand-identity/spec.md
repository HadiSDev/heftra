## ADDED Requirements

### Requirement: The landing site carries the brand

The landing site in `apps/landing` SHALL follow the same brand rules as the web
app. Every favicon and the OG image it serves SHALL be a byte-identical copy of
the file of the same role in `brand/`. It SHALL render the lockup and symbol from
the pack's outlined SVG geometry in `currentColor` resolving to the ink (black on
light surfaces, white on dark), never retype the wordmark, and never recolour,
tint, add effects or gradients to, tilt, stretch or animate the shape of the logo.
Its document head SHALL link `favicon.ico`, `favicon.svg` and
`apple-touch-icon.png` and declare `theme-color` `#0A0A0A`. Motion and depth
effects MAY move the logo's container but SHALL NOT alter the logo itself.

#### Scenario: Served assets trace to the pack

- **WHEN** each favicon and `og-image-1200x630.png` under `apps/landing/public`
  is compared with the file of the same role in `brand/`
- **THEN** the bytes are identical

#### Scenario: Header lockup

- **WHEN** the landing site's navigation renders
- **THEN** it shows the Steelyard lockup as inline SVG with the accessible name
  "Steelyard", no text node of the product name beside it, and in the ink colour
  of the current theme

#### Scenario: No legacy name on the landing site

- **WHEN** `apps/landing/src` is searched case-insensitively for "spend predictor"
  and "erpsaa"
- **THEN** there are no matches
