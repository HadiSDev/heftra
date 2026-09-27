## Context

**Spend data.** Every invoice line carries what an agreement needs to be checked against:
- `item_name`, `description`, `quantity`, `unit`, `unit_price`, `amount`, `discount`, `base_amount`;
- its spend category (`level_1..4`, `spend_category_id`);
- its invoice's `vendor_id`, `invoice_date` and `currency`.

Vendors are global and carry a VAT number (normalised by `vat.international_vat`), a website and a country. Nothing records which employee made a purchase.

**Reading documents.** ai-api reads invoice PDFs in `documents/extractor.py`:
- It uses the pdfplumber text layer first, and renders pages for vision when there is none.
- It prompts with `json_format_hint` and parses with `parse_model`/`json_repair`.
- It runs against the configured vLLM model (Gemma 4 E4B), which has a limited context and makes mistakes on long inputs.

**Background work.** The worker (`worker/loop.py`) claims queued `PipelineRun`s by kind through `EXECUTORS`. When idle, it reads pending invoices on its own.

**Vector search.** `rag/embedding.embed` and Qdrant collections exist. `SectorIndex` shows the "catalogue plus nearest search" pattern.

**Files.** No bytes are stored anywhere today. Invoice PDFs are fetched from the ERP on demand, and `File.storage_path` holds the ERP's reference.

**Reusable UI.** `FileDropzone`, the invoice document viewer, the voucher drawer, `DataTable` and dashboard sections.

## Goals / Non-Goals

**Goals:**
- Upload agreement PDFs and keep them safely, readable again by the worker and the page.
- Draft an agreement's header and terms with the LLM. Every term cites the clause it came from, and nothing is analysed until a person confirms it.
- Find every line an agreement's terms apply to, then work out rule breaks, overcharges, missed discounts, potential savings and commitment progress, each with an amount and a reason.
- Make rule breaks the first thing the report shows, and let a manager accept one as an exception.
- Store findings so the report and the dashboard read quickly, and refresh them when spend or terms change.

**Non-Goals:**
- Knowing which employee bought something.
- Formats other than PDF.
- Alerts.
- Checking supplier stock.
- Editing the PDF.
- Multi-supplier agreements. An agreement has one supplier; a second supplier means a second agreement.

## Decisions

### 1. S3-compatible storage, RustFS locally, behind `FileStore`

`web_api/storage/` defines a `FileStore` protocol:
- `put(key, data, content_type)`
- `get(key) -> bytes`
- `delete(key)`

There are two implementations:
- `S3FileStore` (aioboto3, async). Its settings are `S3_ENDPOINT_URL`, `S3_REGION`, `S3_BUCKET`, `S3_ACCESS_KEY` and `S3_SECRET_KEY`. It uses path-style addressing, which RustFS needs.
- `MemoryFileStore` for tests.

`file_store()` returns the configured one. ai-api imports the same module; it already depends on web-api.

Uploads are stored under `companies/{company_id}/agreements/{agreement_id}/{uuid}.pdf`, recorded as a `File` row with `file_type="agreement_pdf"` and `storage_path` set to the key. Existing ERP `File` rows are untouched.

The browser never gets a bucket URL. `GET /agreements/{id}/document` streams the bytes after the tenant check, as the invoice document endpoint does.

The bucket is created at web-api startup if it's missing, logged and skipped when storage isn't configured. docker compose adds `rustfs/rustfs` on host ports 9100 (S3) and 9101 (console), because 9000 is commonly taken, with a named volume and credentials from the environment.

*Alternatives considered:*
- **Postgres `bytea`:** simple, but it grows the database and backups with documents.
- **Local disk:** doesn't survive more than one host.
- **MinIO:** ruled out by the user.

### 2. Agreements are read like documents, one page per call, with quotes checked

The `Agreement` row carries:
- `read_status`: `pending`, `reading`, `review`, `active`, `failed`;
- `read_attempts`, `read_error` and `read_at`.

After upload the status is `pending`. The worker's idle loop claims pending agreements, as it does invoices (a claim with a stale timeout).

Reading happens in steps:
1. **Text per page:** pdfplumber first. Pages with no text layer are rendered for vision, capped by `AGREEMENT_VISION_MAX_PAGES`.
2. **Header:** from the first pages. The supplier's name, VAT/CVR number and website, the customer party, the reference, the start and end dates, the currency and the governing summary.
3. **Terms:** extracted one page per call, so each prompt fits the model and a reply that can't be parsed costs only its page. Each term has:
   - `kind`, `scope` (a short description of what it covers) and `conditions` (e.g. "when in stock");
   - the kind's fields: `item`, `unit`, `unit_price`, `discount_percent`, `commitment_amount`, `period` and `tiers`. Fields of other kinds are cleared, a missing text field is read as empty, and a commitment without a scope covers all purchases from the supplier;
   - `quote`, the clause verbatim, and its `page`;
   - `confidence`.
4. **Quote check:** a term whose quote isn't found on its page, after whitespace and case folding, is dropped. This is the guard against invented terms, like the emission agent's "only codes a tool showed you".
5. **Merge:** terms of the same kind with the same normalised scope or item, from different pages, are merged, keeping every quote.
6. **Scope categories:** suggested for each term as the company's spend tree categories whose paths are closest to its scope, compared in memory with the embedding model (the tree is small, so neither Qdrant nor `CATEGORY_RETRIEVAL_ENABLED` is needed). Analysis uses the suggested categories for a confirmed term that has none.

When reading finishes, the agreement moves to `review`, with every term in `draft`.

The supplier is linked automatically when the header's VAT number matches a vendor's (`international_vat`). Otherwise it is matched by website root or name keys, and the reviewer confirms or picks the vendor either way.

*Alternative considered:* one prompt over the whole document. It exceeds the model's context on real agreements, and long prompts make a 4B model drop terms.

### 3. Terms are confirmed by a person before they count

`AgreementTerm` has:
- a `status`: `draft`, `confirmed` or `rejected`;
- a `source`: `ai` or `human`;
- the fields above, plus `scope_category_ids` (JSON) and `currency`.

A manager can:
- edit any field;
- confirm or reject a term;
- add a term by hand;
- set the agreement's supplier, dates and currency.

An agreement becomes `active` when its header has a supplier and a start date and at least one term is confirmed. Confirming a term, or editing a confirmed one, requests an analysis run. Every change is audited.

Editing a confirmed term's scope or item clears the cached scope judgements for that term, because the question has changed.

### 4. Candidate retrieval, then a cached LLM scope judge

For each confirmed term of an active agreement, the candidates are the company's lines invoiced within the agreement's validity, with no end date meaning open-ended. A line is a candidate when either:
- its spend category is one of the term's scope categories, or below one; or
- the embedding similarity between the line's text (`item_name`, `description`, category path) and the term's scope or item is at least `AGREEMENT_SIMILARITY_MIN`, taking the top `AGREEMENT_CANDIDATES_MAX` per term.

Line embeddings are computed per run. At the current volume, thousands of lines, that takes seconds. A Qdrant collection per company is the documented next step if it doesn't.

Each (term, candidate) pair is judged by a single-shot prompt. The prompt contains:
- the term's kind, scope, conditions and item;
- the line's item, description, quantity, unit, unit price, category and supplier.

The answer is JSON:
- `in_scope`, `confidence` and `reason`;
- for an agreed price, `same_item` (whether this is the priced item) and `units_comparable` (whether the line's unit is the agreed unit).

Answers are cached in `agreement_scope_cache`, keyed by a hash of the term's judged fields plus the line's `question_key` (the emission matcher's key). Re-running after new lines only judges the new ones. An unparseable answer counts the line as not judged, and the run summary says how many there were.

*Alternatives considered:*
- **An agent with tools per line.** Too slow for thousands of pairs, and the judgement needs no exploration.
- **Pure similarity.** It can't tell "laptop stand" from "laptop".

### 5. Findings are calculated in code and stored

`AgreementFinding` records:
- the agreement, term, invoice line and invoice;
- `kind`, `severity` and `amount` (in the company's base currency);
- `expected` and `actual` (unit prices or percentages in the agreement's currency);
- `quantity`, `reason`, `judge_confidence` and `computed_at`;
- the review: `review_status` (`open`, `exception`, `not_in_scope`), `review_note`, `reviewed_by`, `reviewed_at`.

Supplier identity: a line is from the agreement's supplier when its invoice's vendor is that vendor, or shares its international VAT number.

Findings by kind, for in-scope lines:

| Term | Line from the agreement supplier | Line from another supplier |
|---|---|---|
| Preferred supplier | `compliant` (info) | **`off_contract`** (rule break): amount = line base amount |
| Agreed price, same item, comparable units | unit price converted to the agreement currency at the invoice date (`FxService`); above agreed by more than `AGREEMENT_PRICE_TOLERANCE_PCT` → **`overcharge`** (rule break): amount = (actual − agreed) × quantity, in base currency; otherwise `compliant` | `potential_saving` (info): (actual − agreed) × quantity when positive. It is also an **off-contract** rule break when the agreement has a preferred-supplier term covering the line |
| Agreed price, units not comparable | `price_unverifiable` (warning) | none |
| Discount | discount found on the line (`discount`, or `amount` below `quantity × unit_price`), or as a discount line on the same invoice, of at least the agreed rate minus tolerance → `compliant`; otherwise **`missed_discount`** (warning): amount = rate × line amount | `potential_saving` (info): rate × line amount |
| Volume commitment | counted towards progress, with no finding per line | none |

Commitment progress is a derived figure, not a finding. It is calculated per term and period:
- in-scope spend with the supplier;
- the pro-rata target to date;
- a linear forecast to the period's end;
- the rebate tier reached or next.

Each run recalculates a term's findings and upserts them by (term, line, kind). A line with a `not_in_scope` finding for a term is skipped for that term, and that finding is kept as the record of the decision. A finding that is no longer produced is deleted. A review decision stays with its (term, line, kind), so re-running never reopens an accepted exception. Findings of rejected terms, or of agreements that are deleted, are removed.

*Alternative considered:* computing on read, like emissions. Rejected, because the scope judgement is an LLM answer that must stay stable and reviewable, and the report and dashboard must be fast.

### 6. When analysis runs

Analysis runs as `PipelineRunKind.ANALYSE_AGREEMENTS`, for one company, through the existing worker and run records. It is requested:
- when a term is confirmed or a confirmed term is edited;
- after the company's sync, `read_documents` or `categorize` run succeeds, if it has an active agreement (a system run);
- by a manager through **Re-analyse** (`POST /companies/{id}/agreements/analyse`, `require_management`).

It is deduplicated against a queued run of the same kind. A running analysis has already loaded its terms and lines, so a request made while it runs queues another behind it.

The summary counts:
- terms analysed, candidates, judged, cached and not judged;
- findings by kind.

### 7. API

All routes are under `/api/v1`. Reads are scoped by `tenant_scope`; writes need `require_management` on the company.

| Method | Path | Purpose |
|---|---|---|
| POST | `/companies/{id}/agreements` (multipart `file`) | Upload: PDF only (name and `%PDF` signature), up to `AGREEMENT_MAX_BYTES` (25 MB) → 201, agreement `pending` |
| GET | `/agreements?company_id=` | List with status, supplier, validity, and counts and amounts of open rule breaks |
| GET | `/agreements/{id}` | Header, terms, file info, last analysed |
| PATCH | `/agreements/{id}` | Supplier (vendor id), title, reference, dates, currency |
| DELETE | `/agreements/{id}` | Delete it, its terms, findings and stored file |
| GET | `/agreements/{id}/document` | Stream the PDF |
| POST | `/agreements/{id}/read` | Read again (back to `pending`); drafts are replaced, confirmed terms kept |
| POST | `/agreements/{id}/terms` | Add a term (source `human`) |
| PATCH | `/agreement-terms/{id}` | Edit, confirm or reject |
| GET | `/agreements/{id}/report` | Totals by kind and severity, commitment progress, and the findings page (filters: kind, review status) |
| PATCH | `/agreement-findings/{id}` | Review: `exception` or `not_in_scope` with a note, or reopen |
| GET | `/reports/agreement-compliance?from=&to=&company_id=` | Dashboard: the period's open rule breaks, off-contract spend, overcharges, and the top suppliers bought from off-contract |

### 8. Web

- **Agreements** is added to the main navigation (`routes/_authed/agreements/index.tsx`). It shows:
  - the list, with supplier, validity, a status badge, and open rule breaks with their amount;
  - an upload using `FileDropzone` (PDF, 25 MB).
- **`agreements/$agreementId`** has two tabs:
  - **Terms:** the PDF viewer, reused from invoices, beside the header form and the term cards. Each card shows the kind, fields, quote and page (clicking jumps the viewer to it), and confirm, reject and edit controls. There is also an "Add term" action.
  - **Report:**
    - summary tiles: in-scope spend, share with the supplier, open rule breaks, overcharges, missed discounts, potential savings;
    - the **Rule breaks** table first: date, supplier, item, amount, why, review;
    - price checks and discount checks;
    - commitment progress bars.

  A row opens the voucher drawer for its line. A reading or failed agreement shows its state, with a retry.
- **Dashboard:** a "Contract compliance" section with the period's open rule breaks, off-contract spend and top off-contract suppliers, linking to Agreements.

## Risks / Trade-offs

- **[The 4B model misreads a clause or invents one]** → Quotes are checked against the page, every term needs a person's confirmation, and the review shows the quote beside the PDF.
- **[Scope judgements are wrong at the edges]** → Every finding carries the judge's reason and confidence. Managers can mark a finding as not in scope, and that decision persists. Low-confidence judgements are labelled.
- **[Units differ: box of 10 against each]** → Those lines get `price_unverifiable` rather than an overcharge.
- **["When in stock" and similar conditions can't be verified]** → The condition is shown on every off-contract finding, and the manager can record it as an exception.
- **[Many pairs to judge on a large company]** → Candidate retrieval caps the pairs per term, answers are cached, and runs are incremental. The summary shows the counts so it can be tuned.
- **[A rule break names no person]** → The finding links to the voucher and the invoice document, which usually shows a reference or the person it was addressed to. Attribution is recorded as an open question.
- **[Storage is unavailable]** → Upload fails with a clear 503, and reading marks the agreement failed with the storage error. Nothing half-created is left: the row and the object are written in that order, and the row is removed if the put fails.

## Migration Plan

1. The user adds the RustFS service (`docker compose up -d rustfs`), sets the S3 settings, syncs dependencies (`aioboto3`) and runs migration `0020_trade_agreements`.
2. Deploy web-api and ai-api. The bucket is created at startup.
3. Upload an agreement, review it, and confirm its terms. Analysis runs by itself.

To roll back, hide the navigation entry and stop queuing `analyse_agreements`. The tables and the bucket are additive.

## Open Questions

- **Attributing rule breaks to employees:** could come from the invoice's "Your reference" or "Att." field, read during document processing, or from ERP expense-claim data. Deferred.
- **Alerts:** should a new off-contract rule break notify someone, and by e-mail or in-app? Deferred.
- **Retention:** should a deleted agreement's file be kept for audit? The design deletes it; a soft delete could follow.
