## ADDED Requirements

### Requirement: A manager SHALL be able to upload an agreement for a company

`POST /api/v1/companies/{id}/agreements` SHALL accept a multipart `file` from a manager of the company: a system admin, organization admin or moderator. It SHALL:
- accept only a PDF, checked by name and by the `%PDF` signature, responding 422 otherwise;
- respond 413 when the file is over the configured limit (25 MB by default);
- store the file;
- create an agreement with status `pending`, named after the file until its title is read;
- respond `201 Created` with the agreement.

Other callers SHALL get 403, and a company outside the caller's organization 404. The upload SHALL be audited.

#### Scenario: Uploading a framework agreement

- **WHEN** a manager uploads `Atea framework 2026.pdf` for their company
- **THEN** the response is 201 with a `pending` agreement, and the file is stored

#### Scenario: A viewer can't upload

- **WHEN** a viewer uploads an agreement
- **THEN** the response is 403 and nothing is stored

#### Scenario: Not a PDF

- **WHEN** a manager uploads `terms.docx`
- **THEN** the response is 422 and nothing is stored

### Requirement: The worker SHALL read pending agreements into a header and draft terms

The worker SHALL claim pending agreements when it has no queued run, as it does pending documents. Reading SHALL move an agreement from `pending` to `reading`, then to `review` on success or `failed` on failure. A failure SHALL record the error and the attempt count, and SHALL be retried up to a limit.

Reading SHALL take each page's text from its text layer, using vision for pages without one. It SHALL extract:
- **the header:** the supplier's name, VAT or CVR number and website, the reference, the title, the start and end dates, and the currency;
- **the terms**, a few pages at a time. Each term SHALL have:
  - a kind: `preferred_supplier`, `agreed_price`, `discount` or `volume_commitment`;
  - its scope, and any conditions;
  - the fields its kind needs: item and unit price for an agreed price; percentage for a discount; amount, period and optional rebate tiers for a volume commitment;
  - the clause it came from, quoted verbatim, with its page number;
  - a confidence.

A term whose quote isn't found on its page SHALL be dropped. Terms SHALL be read one page per call, and terms repeated across pages SHALL be merged. The words a page defines SHALL be read with it, kept only when their meaning is found on that page, and written into the scope of every term that uses them, whichever page the term is on. Each term SHALL be given suggested spend categories from the company's tree.

The supplier SHALL be linked to a known vendor with the same international VAT number when there is one, and suggested by website or name otherwise. All extracted terms SHALL be stored as `draft` with source `ai`.

#### Scenario: A framework agreement is read

- **WHEN** the worker reads an agreement that says "IT equipment shall be purchased from Atea when available from stock" on page 3, and "Lenovo ThinkPad T14 Gen 5: DKK 8,000 per unit" on page 7
- **THEN** the agreement is in `review` with a `preferred_supplier` term scoped to IT equipment, conditioned on stock, quoting page 3; and an `agreed_price` term for the ThinkPad T14 Gen 5 at DKK 8,000, quoting page 7; both `draft`

#### Scenario: An invented clause is dropped

- **WHEN** the model returns a term whose quote appears nowhere on its page
- **THEN** that term is not stored

#### Scenario: The supplier is recognised

- **WHEN** the agreement's supplier VAT number is DK12345678 and a vendor has that number
- **THEN** the agreement is linked to that vendor

#### Scenario: Reading fails

- **WHEN** the file can't be read from storage or the model's answer can't be parsed after the retries
- **THEN** the agreement is `failed` with the error, and can be read again on request

### Requirement: A manager SHALL review an agreement's header and terms before they count

A manager SHALL be able to:
- set the agreement's supplier (a vendor), title, reference, start and end dates and currency;
- edit any field of a term;
- confirm or reject a term;
- add a term by hand, with source `human`.

Only `confirmed` terms SHALL be analysed. An agreement SHALL become `active` when it has a supplier, a start date and at least one confirmed term. Every change SHALL be audited with the user who made it.

Reading an agreement again SHALL replace its `draft` terms and keep its confirmed and rejected ones.

#### Scenario: Confirming a term

- **WHEN** a manager corrects a draft term's price to DKK 7,950 and confirms it, on an agreement with a supplier and a start date
- **THEN** the term is `confirmed` at DKK 7,950, the agreement is `active`, and an analysis is requested

#### Scenario: A rejected term is ignored

- **WHEN** a manager rejects a term
- **THEN** it is kept as `rejected` and never analysed

#### Scenario: Reading again keeps decisions

- **WHEN** an agreement with one confirmed and two draft terms is read again
- **THEN** the confirmed term is unchanged, and the drafts are replaced by the new reading's

### Requirement: Agreements SHALL be listed, shown and deleted within the caller's companies

- `GET /api/v1/agreements` SHALL list the agreements of the caller's companies. Each SHALL have its supplier, validity, status, and the count and amount of its open rule breaks.
- `GET /api/v1/agreements/{id}` SHALL return its header, terms and file details.
- `GET /api/v1/agreements/{id}/document` SHALL stream its PDF.
- A manager SHALL be able to delete an agreement, which SHALL delete its terms, findings and stored file.

An agreement of a company outside the caller's organization SHALL get 404 on every route.

#### Scenario: The list shows rule breaks

- **WHEN** a company has an active agreement with three open off-contract findings totalling DKK 21,400
- **THEN** its row in the list shows 3 rule breaks and DKK 21,400

#### Scenario: Deleting an agreement

- **WHEN** a manager deletes an agreement
- **THEN** its terms, findings and stored file are gone
