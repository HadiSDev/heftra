## ADDED Requirements

### Requirement: Agreements SHALL be listed and uploaded from their page

The `/agreements` page SHALL list the agreements of the chosen company, or of all the user's companies. For each it SHALL show:
- its title and supplier;
- its validity;
- a status badge: reading, needs review, active, expired or failed;
- its open rule breaks with their amount.

Rule breaks SHALL be emphasised when there are any. Managers SHALL be able to upload a PDF with the UI library's file dropzone (PDF, up to 25 MB). The new agreement SHALL appear at once, as reading. The page SHALL have loading, empty, error and retry states.

#### Scenario: Uploading

- **WHEN** a manager drops a PDF onto the upload area
- **THEN** the agreement appears in the list as reading, and becomes "needs review" when the worker has read it

#### Scenario: A viewer

- **WHEN** a viewer opens Agreements
- **THEN** they see the list and reports, but no upload or review controls

### Requirement: An agreement's terms SHALL be reviewed next to its document

The agreement page's **Terms** tab SHALL show the PDF beside:
- the header form: supplier picker, title, reference, dates, currency;
- one card per term, showing its kind, scope, conditions and the kind's fields, its quote and page, and its source and status.

Choosing a term's quote SHALL scroll the document to its page. A manager SHALL be able to:
- edit and confirm or reject each term;
- add a term;
- save the header;
- read the document again.

A reading or failed agreement SHALL say so, and a failed one SHALL offer to read it again.

#### Scenario: Reviewing a draft

- **WHEN** a manager opens an agreement in review, corrects a term's price and confirms it
- **THEN** the card shows the term as confirmed, and the agreement becomes active once it has a supplier and a start date

#### Scenario: Checking a quote

- **WHEN** a reviewer chooses the quote of a term from page 7
- **THEN** the document scrolls to page 7

### Requirement: The agreement report SHALL lead with rule breaks

The agreement page's **Report** tab SHALL show:
- summary figures: in-scope spend, the share with the supplier, open rule breaks with their amount, overcharges, missed discounts and potential savings;
- then a **Rule breaks** table: date, supplier, item, amount, the reason, and the term's conditions;
- then price checks, discount checks and commitment progress.

Each finding SHALL open its line's voucher in the voucher drawer. A manager SHALL be able to mark a finding as an exception or not in scope with a note, or reopen it. The report SHALL say when it was last analysed, and SHALL offer managers a **Check again** action. While the company's analysis is queued or running, the report SHALL say so, the action SHALL be unavailable, and the page SHALL poll until it finishes and then refresh its figures. When the last analysis failed, the report SHALL say so with its error. `GET /agreements/{id}` SHALL carry the company's latest analysis (its status, times and error) for this.

#### Scenario: Following up a rule break

- **WHEN** a manager opens a rule break for a laptop bought from Proshop
- **THEN** the voucher drawer opens on that line, and the manager can mark the finding as an exception with a note

#### Scenario: Commitment progress

- **WHEN** an agreement has a yearly volume commitment
- **THEN** the report shows its progress against the pro-rata target and the forecast, with the rebate tier reached
