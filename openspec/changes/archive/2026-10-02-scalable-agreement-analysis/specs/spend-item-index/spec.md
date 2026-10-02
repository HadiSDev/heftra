## ADDED Requirements

### Requirement: A company's lines SHALL be grouped into distinct items

A company's invoice lines SHALL be grouped into **items**. An item is what was bought: the line's item name, description, unit, spend category and the invoice's vendor, normalised for case and spacing. Every line SHALL map to exactly one item through its `item_key`, a digest of those fields. The grouping SHALL be done in the database, without loading the lines into memory.

An item SHALL carry:
- its text;
- its category path and supplier;
- how many lines it covers;
- their net spend in base currency;
- the dates of its first and last line.

#### Scenario: Repeated purchases are one item

- **WHEN** a company has 12,000 lines "Magic Keyboard Touch ID (MXK73DK/A)" from CS-Online in the same category
- **THEN** they are one item covering 12,000 lines, with their total spend and date range

#### Scenario: The same product from another supplier is another item

- **WHEN** the same keyboard is also bought from Proshop
- **THEN** that is a separate item, so the supplier rule can be judged for each

### Requirement: Items SHALL be embedded once and searchable by similarity

Each item SHALL be embedded once, when first seen, and stored in a Qdrant collection per company. Its payload SHALL hold:
- its `item_key`;
- its category id;
- its vendor id;
- its first and last line dates.

Indexing SHALL be incremental: only items not yet indexed are embedded. A search SHALL return the items most similar to a text, above a threshold and up to a limit, optionally filtered by category ids and by a date range overlapping the item's.

When Qdrant can't be reached, indexing SHALL be skipped and logged, and similarity search SHALL return nothing; analysis then proceeds by category alone and says so in its run summary.

#### Scenario: Only new items are embedded

- **WHEN** a sync adds 50,000 lines of which 40 are new items
- **THEN** 40 items are embedded and the rest of the index is untouched

#### Scenario: Qdrant is down

- **WHEN** the index can't be reached during analysis
- **THEN** candidates come from categories only and the run's summary records that similarity was unavailable
