## 1. Storage (infra + web-api)

- [x] 1.1 Add a `rustfs` service to `docker-compose.yml`. Pin its image, check its credential variables against the RustFS docs, and give it host ports 9100 (S3) and 9101 (console) and a named volume. Document `S3_ENDPOINT_URL`, `S3_REGION`, `S3_BUCKET`, `S3_ACCESS_KEY` and `S3_SECRET_KEY` in `.env.example`. Don't start it; the user runs compose
- [x] 1.2 Declare `aioboto3` in web-api's dependencies (the user runs the sync)
- [x] 1.3 `web_api/storage/`:
  - [x] 1.3.1 The `FileStore` protocol and `StorageUnavailable`
  - [x] 1.3.2 `S3FileStore`, path-style with timeouts
  - [x] 1.3.3 `MemoryFileStore`
  - [x] 1.3.4 `file_store()` from config, and `ensure_bucket`
  - [x] 1.3.5 Tests, with the memory store and a stubbed aioboto3 client
- [x] 1.4 Create the bucket at startup in the app lifespan, logged and skipped when unavailable (test)

## 2. Agreements data and API (web-api)

- [x] 2.1 Models, one file each: `Agreement`, `AgreementTerm`, `AgreementFinding`, `AgreementScopeJudgement` (the cache). Put the enums in `enums.py`, and add `File.file_type="agreement_pdf"`. Migration `0020_trade_agreements`; don't run it
- [x] 2.2 Company deletion removes its agreements, terms, findings, judgements and stored files (test)
- [x] 2.3 Schemas under `schemas/agreements/`: agreement, term (create and patch per kind), finding, report, compliance report
- [x] 2.4 Upload: `POST /companies/{id}/agreements`:
  - [x] 2.4.1 Checks: management only, PDF name and signature, size limit
  - [x] 2.4.2 The row first, then the object; remove the row if the put fails (503)
  - [x] 2.4.3 Audited
  - [x] 2.4.4 Tests: 201, 403, 404, 413, 422, 503
- [x] 2.5 List, detail, patch (header), delete, document stream, and read-again, with tenant scoping and audit (tests)
- [x] 2.6 Terms: add, patch (edit, confirm, reject), and the `active` rule. Confirming or editing requests `analyse_agreements`. Editing a scope or item clears that term's judgements (tests)
- [x] 2.7 Findings review: `PATCH /agreement-findings/{id}`; later runs skip a line for a term once one of its findings is `not_in_scope` (tests)
- [x] 2.8 `POST /companies/{id}/agreements/analyse` (management), deduplicated against an unfinished run (test)
- [x] 2.9 Report: `GET /agreements/{id}/report`:
  - [x] 2.9.1 Totals by kind and severity
  - [x] 2.9.2 In-scope spend and the share with the supplier
  - [x] 2.9.3 Commitment progress
  - [x] 2.9.4 The findings, filtered and ordered with rule breaks first
  - [x] 2.9.5 Tests
- [x] 2.10 `GET /reports/agreement-compliance`, for the dashboard (tests)
- [x] 2.11 `PipelineRunKind.ANALYSE_AGREEMENTS`

## 3. Reading agreements (ai-api)

- [x] 3.1 `agreements/pages.py`: text per page with pdfplumber, and vision for pages without text, capped (tests with small generated PDFs)
- [x] 3.2 `agreements/models.py`: the pydantic models for the header and each term kind
- [x] 3.3 `agreements/prompts.py` and `agreements/extract.py`:
  - [x] 3.3.1 The header from the first pages, and terms chunk by chunk
  - [x] 3.3.2 Parse with `parse_model`
  - [x] 3.3.3 The quote check against the page
  - [x] 3.3.4 Merge across chunks
  - [x] 3.3.5 Tests with a stub LLM: an invented quote dropped, duplicates merged, a malformed answer
- [x] 3.4 `agreements/supplier.py`: link by international VAT, then suggest by website root or name keys (tests)
- [x] 3.5 `agreements/scope_categories.py`: suggest spend categories for a term from the company's tree index (test)
- [x] 3.6 `agreements/runner.py`:
  - [x] 3.6.1 Claim pending or stale agreements
  - [x] 3.6.2 Read them from `FileStore`
  - [x] 3.6.3 Store the header and draft terms, replacing drafts and keeping confirmed and rejected terms
  - [x] 3.6.4 Handle attempts and failure
  - [x] 3.6.5 Wire into the worker's idle loop after documents
  - [x] 3.6.6 Tests

## 4. Compliance analysis (ai-api)

- [x] 4.1 `compliance/candidates.py`: the lines within validity, by scope categories and their descendants, plus the top-K by embedding similarity above the threshold (tests with a fake embedder)
- [x] 4.2 `compliance/judge/`: the prompt, the parsed reply (in scope, confidence, reason, same item, comparable units), and the cache keyed by the term's judged fields and the line's `question_key` (tests: parse failures, cache hits)
- [x] 4.3 `compliance/supplier_identity.py`: same vendor, or the same international VAT (test)
- [x] 4.4 `compliance/findings.py`: deterministic findings per kind, following the design's table. Convert prices with `FxService` at the invoice date, apply tolerances, and detect discounts on the line or the invoice (tests for every row of the table, including incomparable units and the preferred-supplier plus agreed-price overlap)
- [x] 4.5 `compliance/commitments.py`: the period, spend to date, the pro-rata target, the forecast and the tiers (tests)
- [x] 4.6 `compliance/run.py` `analyse_company`:
  - [x] 4.6.1 Upsert findings by (term, line, kind), keeping reviews
  - [x] 4.6.2 Delete what's no longer produced, and the findings of rejected terms
  - [x] 4.6.3 The summary counts
  - [x] 4.6.4 Tests: re-runs are incremental, an exception survives, not-in-scope is learnt
- [x] 4.7 Register the `analyse_agreements` executor. Queue a system run after a successful sync, `read_documents` or `categorize` when the company has an active agreement (tests)
- [x] 4.8 Config and `.env.example`:
  - `AGREEMENT_CHUNK_PAGES`
  - `AGREEMENT_VISION_MAX_PAGES`
  - `AGREEMENT_SIMILARITY_MIN`
  - `AGREEMENT_CANDIDATES_MAX`
  - `AGREEMENT_PRICE_TOLERANCE_PCT`
  - `AGREEMENT_DISCOUNT_TOLERANCE_PCT`
  - `AGREEMENT_MAX_BYTES`
  - `AGREEMENT_MAX_ATTEMPTS`

## 5. Web

- [x] 5.1 Types and queries in `lib/api/agreements.ts` (and types): list, detail, report and compliance report. Mutations for upload (with progress), header, terms, findings review, read again, re-analyse and delete, each invalidating what it changes. Poll while an agreement is reading or an analysis is unfinished
- [x] 5.2 The nav entry **Agreements** after Suppliers (test)
- [x] 5.3 `routes/_authed/agreements/index.tsx` and `components/agreements/list/`: the table with status badges and emphasised rule breaks, the `FileDropzone` upload for managers, and the loading, empty and error states (tests)
- [x] 5.4 `routes/_authed/agreements/$agreementId.tsx` with Terms and Report tabs (search param `tab`)
- [x] 5.5 `components/agreements/terms/`:
  - [x] 5.5.1 The document viewer, reused
  - [x] 5.5.2 The header form, with the supplier picker from the vendors search
  - [x] 5.5.3 A term card per kind: edit, confirm, reject; the quote jumps to its page
  - [x] 5.5.4 The add-term dialog
  - [x] 5.5.5 The reading and failed states, with read-again
  - [x] 5.5.6 Tests
- [x] 5.6 `components/agreements/report/`:
  - [x] 5.6.1 The summary tiles
  - [x] 5.6.2 The rule-breaks table first, then price checks, discount checks and commitment progress
  - [x] 5.6.3 The finding review popover (exception or not in scope, with a note)
  - [x] 5.6.4 Opening the voucher drawer for a finding
  - [x] 5.6.5 Re-analyse and last analysed
  - [x] 5.6.6 Tests
- [x] 5.7 The dashboard's **Contract compliance** section, with an empty state that invites an upload (tests)
- [x] 5.8 Run vitest, tsc, eslint and prettier on the changed files, and regenerate the route tree

## 6. Verification

- [x] 6.1 Run the web-api and ai-api suites in full
- [ ] 6.2 With the user's go-ahead: start RustFS, run the migration, upload a real or sample framework agreement, review its terms and confirm them. Check the rule breaks against a few lines by hand
- [ ] 6.3 Browser check with an impersonated manager: upload, review, the report, a finding's voucher, marking an exception, and the dashboard section
