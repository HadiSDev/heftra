## ADDED Requirements

### Requirement: The benchmark SHALL pool what organizations pay per product and specification

The **price benchmark** SHALL hold, for each product (see `product-alternatives`) and for each group of items with the same class, pricing unit and key attributes, the unit prices that organizations paid in the last 12 months: one price per organization, its spend-weighted unit price in a common currency, without VAT. It SHALL be refreshed from the items' unit prices when they change.

A benchmark SHALL give the median and the lowest quartile of those prices, and how many organizations they come from.

#### Scenario: A product's benchmark

- **WHEN** six organizations bought part number MXK73DK/A in the last year at DKK 980, 999, 1,010, 1,050, 1,136 and 1,190 each
- **THEN** its benchmark has 6 organizations, a median of DKK 1,030 and a lowest quartile of DKK 1,001.75

### Requirement: A benchmark SHALL be shown only from at least three organizations, and anonymously

A benchmark SHALL be used only when it comes from at least `BENCHMARK_MIN_ORGANIZATIONS` organizations (default 3, never fewer than 3) other than the one viewing it. It SHALL never name an organization, a company, a supplier, or show a single organization's price, and the viewing organization's own price SHALL be left out of what it is shown.

#### Scenario: Too few organizations

- **WHEN** only two other organizations bought a product
- **THEN** no benchmark is shown for it

#### Scenario: Nothing names a buyer

- **WHEN** a benchmark is shown as an alternative
- **THEN** it gives the median, the lowest quartile and the number of organizations, and nothing else about them

### Requirement: An organization SHALL choose whether to take part

An organization SHALL have a setting to take part in the price benchmark, on by default. An organization that doesn't take part SHALL contribute no prices and SHALL be shown no benchmark. Only an organization admin SHALL change it, and the change SHALL be audited. Turning it off SHALL remove the organization's prices from the benchmark at its next refresh.

#### Scenario: Opting out

- **WHEN** an organization admin turns the benchmark off
- **THEN** the organization's prices leave the benchmark at its next refresh, and its items get no benchmark alternatives
