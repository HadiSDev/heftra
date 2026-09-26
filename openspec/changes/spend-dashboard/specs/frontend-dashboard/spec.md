## ADDED Requirements

### Requirement: The dashboard SHALL be read for a period and a company chosen in the URL

The dashboard SHALL offer a period of this month, this quarter, year to date, last 12 months, or a custom range, defaulting to year to date, and a company filter defaulting to every company; both SHALL be kept in the URL, so a view can be shared and survives a reload, and unknown values SHALL be ignored. Every figure SHALL be for the chosen period and company, and each change SHALL be against the comparison period the API uses (the same days as many calendar months earlier for a period starting on the first of a month, otherwise as many days before), named in the page (for example "vs 1 Apr – 26 Jun").

#### Scenario: Choosing a quarter

- **WHEN** the user chooses "This quarter" on 26 September 2026
- **THEN** the URL holds the period, every figure covers 1 July – 26 September 2026, and changes are against 1 April – 26 June 2026

#### Scenario: A shared link

- **WHEN** a user opens a dashboard link carrying a company and a custom range
- **THEN** the page shows that company and range

### Requirement: The tiles SHALL say what was spent, how much is categorized, what needs attention and with how many suppliers

The dashboard SHALL show four tiles, per base currency where they carry money:

- **Spend**: the period's spend, its change from the comparison period as a percentage with a rise or fall marker, and a sparkline of the twelve months ending with the period;
- **Categorized**: the categorized share of the period's spend with a progress bar, linking to Spend Lines;
- **Needs attention**: the counts of lines to review, documents that failed and invoices whose total disagrees with the ERP, each linking to Spend Lines filtered to them, or "All clear" when all are zero;
- **Suppliers**: how many had spend in the period and how many are new, linking to Suppliers.

A change SHALL be shown as "New" when the comparison period had no spend, and no change SHALL be shown when neither had any.

#### Scenario: Spend is up

- **WHEN** the period's spend is DKK 12,000 against DKK 10,000
- **THEN** the Spend tile shows DKK 12,000 and a 20% rise

#### Scenario: Nothing needs attention

- **WHEN** no line needs review, no document failed and no total disagrees
- **THEN** the Needs attention tile says "All clear"

### Requirement: The dashboard SHALL chart monthly spend by its top categories

The dashboard SHALL show twelve monthly bars ending with the period's last month, stacked by the top categories with "Other" and "Not categorized" last, with a legend, a tooltip per month giving each category's spend, and each currency charted apart. The chart SHALL keep its height while loading and SHALL describe itself to assistive technology by a text summary.

#### Scenario: Reading a month

- **WHEN** the user points at August's bar
- **THEN** a tooltip lists August's spend per category and in total

### Requirement: The dashboard SHALL break spend down by category and by supplier

The dashboard SHALL show spend by category, largest first, each with its amount, its share of the period's spend as a bar, and its change, and each expandable to its subcategories; and the top ten suppliers, each with amount, share and change, opening the supplier's page when chosen. "Not categorized" SHALL appear as a category, last.

#### Scenario: Drilling into a category

- **WHEN** the user expands Technology
- **THEN** its subcategories are listed beneath it with their amounts and changes

#### Scenario: From the dashboard to a supplier

- **WHEN** the user chooses a supplier in Top suppliers
- **THEN** the supplier's page opens

### Requirement: The dashboard SHALL list insights worth a look

The dashboard SHALL list the insights the API returns under New suppliers, Biggest increases, Recurring spend and Largest uncategorized, each item linking to the supplier's page or to the voucher in Spend Lines, and SHALL leave out a heading with nothing under it.

#### Scenario: A recurring supplier

- **WHEN** a supplier has spend in four of the last six months averaging DKK 400
- **THEN** it is listed under Recurring spend as about DKK 400 a month

### Requirement: The dashboard SHALL have loading, empty and error states and no layout shift

Each section SHALL hold its place with a placeholder of its final size while loading, so the page does not shift when data arrives or the period changes; the previous figures SHALL stay in view while a new period loads. With no spend in the period the page SHALL say so and offer "Last 12 months"; a failed section SHALL show an error in its place without hiding the others. The page SHALL work at phone width without horizontal scrolling.

#### Scenario: A period with no spend

- **WHEN** the chosen period has no spend
- **THEN** the page says there was no spend in it and offers to show the last 12 months

#### Scenario: One report fails

- **WHEN** the insights request fails and the others succeed
- **THEN** the insights section shows an error and the tiles, chart and breakdowns still show
