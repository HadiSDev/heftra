## ADDED Requirements

### Requirement: An item SHALL have a specification, extracted once

Each item a company buys (see `spend-item-index`) SHALL get a **specification** read by the LLM from the item's name, description, unit, spend category and supplier. A specification holds:
- its **class**: `material` (bought by weight, length, area, volume or as stock to be processed: steel, wood, cable by the metre), `part` (a component bought by the piece to be built into something or to maintain a machine, usually known by its maker's part number: bearings, screws, connectors, motors, valves, filters, cutting inserts, spare parts), `finished_good` (bought to be used as it is: toilet paper, laptops, snacks, smartphones) or `service` (not a physical product: a service, fee, subscription, licence, insurance, travel, shipping, rent, utility or tax);
- a short **product name** in English;
- its **identifiers**, each when stated: manufacturer part number, EAN/GTIN, brand, model;
- its **product type**: what kind of product it is, for what use (a business laptop, a hot-rolled round bar, an installation cable);
- its **key attributes**: what a buyer must not get less of. Each attribute has a name, a value and a kind:
  - **numeric**, with its unit and whether more is better, less is better or it must be equal;
  - **tiered**, with its family, tier and generation, for parts sold in ranked lines: a processor (Intel Core, i7, 13th generation), a graphics card, a steel or quality grade;
  - **other**, for anything else (a material, a coating, a certification).

  For example: a steel bar's grade, form, diameter and length; a laptop's processor, memory, storage and screen size; a toilet roll's ply and sheets per roll;
- its **pricing unit**: one of `kg`, `m`, `m2`, `m3`, `l`, `piece`, `sheet`, `roll`, `pack`;
- **units per line unit**: how many pricing units one unit of the line holds, when it can be told. "Pack of 8 rolls" with pricing unit `roll` is 8; "box of 305 m" with pricing unit `m` is 305;
- a **confidence** from 0 to 1.

When an item is priced per kg, l or m, the reader gave no pack size or one, and its lines aren't bought in that measure, a size its unit, name or description states in that measure (10 g, 250 ml, 305 m) SHALL be its pack size; a rate such as 80 g / m² SHALL NOT count.

A specification SHALL be extracted only once per item, and again only when the item's text changes; it SHALL be stored with the item. An item whose specification cannot be read SHALL be retried on a later run, and counted.

#### Scenario: A cable sold by the box

- **WHEN** an item is "Cat6 U/UTP installationskabel LSZH 305m kasse" bought per "stk"
- **THEN** its class is `material`, its pricing unit is `m`, its units per line unit is 305, and its key attributes include the category Cat6, shielding U/UTP and jacket LSZH

#### Scenario: A laptop

- **WHEN** an item is "Lenovo ThinkPad T14 Gen 5 21ML003XMX, Ultra 7 155U, 16GB, 512GB SSD"
- **THEN** its class is `finished_good`, its product type is a business laptop, its model is ThinkPad T14 Gen 5, its part number is 21ML003XMX, its pricing unit is `piece`, and its key attributes include the processor as tiered (Intel Core Ultra, tier 7, series 1) and 16 GB memory and 512 GB storage, more being better

#### Scenario: A bearing is a part

- **WHEN** an item is "SKF 6204-2RSH kugleleje 20x47x14"
- **THEN** its class is `part`, its brand is SKF, its part number is 6204-2RSH, its pricing unit is `piece`, and its key attributes include its bore, outer diameter and width, each to be equal, and its sealing

#### Scenario: Insurance is a service

- **WHEN** an item is "Ansvarsforsikring Erhvervsansvar"
- **THEN** its class is `service`

#### Scenario: A size in the name is the pack size

- **WHEN** an item "THERMAL HERO Wärmeleitpaste - 10g" bought per piece is read as priced per kg, and the reader gives no pack size or one
- **THEN** its units per line unit is 0.01, taken from the size its name states

#### Scenario: Toilet paper by the pack

- **WHEN** an item is "Lotus Professional toiletpapir 2-lag 8 ruller x 50 m"
- **THEN** its pricing unit is `roll` with 8 per line unit, and its key attributes include 2 ply and 50 m per roll

#### Scenario: Only new items are read

- **WHEN** a scan runs after a sync that added 40 new items to a company with 3,000 specified items
- **THEN** only the 40 new items' specifications are extracted

### Requirement: A specification SHALL be correctable by a person

A manager SHALL be able to correct an item's specification: its class, identifiers, key attributes, pricing unit and units per line unit. A corrected specification SHALL be marked as set by a person, SHALL NOT be overwritten by extraction, and SHALL make the item's alternatives be found again. The change SHALL be audited.

#### Scenario: A wrong pack size is corrected

- **WHEN** a manager changes an item's units per line unit from 1 to 8 rolls
- **THEN** the item's price per roll is divided by 8, its alternatives are found again, and a later extraction leaves the correction in place

### Requirement: An item SHALL have a price per pricing unit

An item's **unit price** SHALL be its net spend in base currency over the last 12 months divided by the quantity bought in that time, in pricing units: each line's quantity times the units per line unit. Lines without a quantity SHALL be left out of the price and counted. An item with no units per line unit, or no line with a quantity, SHALL have no unit price and SHALL NOT get alternatives with a saving; it SHALL say why.

The item SHALL also carry its **yearly quantity**: the pricing units bought in the last 12 months.

#### Scenario: Price per metre of a cable box

- **WHEN** a company bought 4 boxes of 305 m Cat6 cable for DKK 3,660 in the last year
- **THEN** the item's unit price is DKK 3 per metre and its yearly quantity is 1,220 m

#### Scenario: No quantity

- **WHEN** an item's lines carry an amount but no quantity
- **THEN** the item has no unit price, says the quantity is missing, and gets no saving
