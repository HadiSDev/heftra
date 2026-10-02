## ADDED Requirements

### Requirement: Items SHALL be stored with their specification and product

Each item SHALL be stored as a row per company and item key, refreshed when its lines change. The row SHALL hold:
- the item's text, supplier and category;
- its specification and who set it (see `item-specifications`);
- its product, when it has one (see `product-alternatives`);
- its unit price, yearly quantity and 12-month spend in base currency;
- when its alternatives were last searched.

Items SHALL also be embedded by their specification into one index shared by all companies, whose payload holds the organization, the company, the class and the pricing unit, so that equivalent items can be found within the organization and across organizations. A search SHALL be able to filter by class, pricing unit and organization.

#### Scenario: An item keeps its specification across syncs

- **WHEN** a sync adds new lines to an item that already has a specification
- **THEN** the item's unit price, yearly quantity and spend are refreshed, and its specification is kept

#### Scenario: Equivalent items are found across companies

- **WHEN** two companies of different organizations buy 20 mm S235JR round bar from different suppliers
- **THEN** a search of the specification index finds both, each with its organization, class and pricing unit
