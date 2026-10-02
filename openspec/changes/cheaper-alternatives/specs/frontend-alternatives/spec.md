## ADDED Requirements

### Requirement: An Alternatives page SHALL list items with savings, largest first

The sidebar SHALL have an **Alternatives** entry. Its page SHALL list the items of the selected companies that have at least one open alternative, ranked by their best yearly saving, with for each:
- the item's product name, supplier and class (material or finished good);
- its unit price per pricing unit and its yearly quantity;
- its best alternative's unit price, source (your purchases, other customers, marketplaces) and match (exact or equivalent);
- the best yearly saving, in base currency.

The page SHALL total the best savings of the listed items, SHALL filter by company, source, match and class, and SHALL be paged. With nothing found yet it SHALL say whether a scan is still to run or found nothing.

#### Scenario: The largest saving leads

- **WHEN** a company has alternatives saving DKK 732 on cable and DKK 4,200 on laptops
- **THEN** the laptops are listed first, and the page totals DKK 4,932

#### Scenario: Only marketplace offers

- **WHEN** a person filters by the marketplace source
- **THEN** only items whose open alternatives include a marketplace offer are listed, ranked by their best marketplace saving

### Requirement: An item's view SHALL show its specification and its alternatives

Opening an item SHALL show:
- its specification: class, identifiers, key attributes, pricing unit and units per line unit, saying whether it was read by AI or set by a person;
- its unit price and yearly quantity, or why it has none;
- its alternatives, best saving first. Each shows its source and match, its unit price and yearly saving, the attributes compared side by side marked same, better or worse, and its origin: the supplier and when it was bought, the number of organizations, or the connector and seller with a link to the offer and when it was seen;
- what an alternative would break under an agreement, when it would;
- when the item was last searched, and whether a search is running.

A manager SHALL be able to correct the specification there.

#### Scenario: Attributes side by side

- **WHEN** a person opens a steel bar item with an equivalent alternative in a better grade
- **THEN** the grade row shows S235JR beside S355J2, marked better, and the other attributes marked same

### Requirement: A person SHALL be able to ask for alternatives and review them

A manager SHALL have a **Find cheaper alternatives** action on an item, on the Alternatives page and on a spend line's item, which queues a search and shows that it is running until it finishes. A manager SHALL be able to dismiss an alternative with a reason and a note, mark it as switched, and reopen it. Viewers SHALL see alternatives but no actions.

#### Scenario: Asking from a spend line

- **WHEN** a manager opens a spend line and chooses Find cheaper alternatives
- **THEN** a search for the line's item is queued, the item shows it is being searched, and its alternatives appear when it finishes

#### Scenario: A viewer

- **WHEN** a viewer opens an item with alternatives
- **THEN** they see the alternatives, with no action to search, dismiss or switch

### Requirement: The organization's settings SHALL include the price benchmark

The organization settings SHALL show whether the organization takes part in the price benchmark, what it shares (prices only, as anonymous aggregates of at least three organizations) and what it gets, and SHALL let an organization admin turn it on or off.

#### Scenario: An admin opts out

- **WHEN** an organization admin turns the benchmark off in the settings
- **THEN** the setting is saved, and the page says the organization's items get no benchmark alternatives
