## 0. Prerequisite

- [x] 0.1 Archive `trade-agreements` (with its spec sync) so `agreement-compliance` is in `openspec/specs/`. Ask the user first: its tasks 6.2 and 6.3 are still open

## 1. Baseline benchmark

- [x] 1.1 `apps/ai-api/scripts/agreement_benchmark.py`:
  - [x] 1.1.1 A synthetic company from the deterministic synthetic catalog: N lines (default 1,000,000), about 20,000 items, 40 suppliers, 3 years
  - [x] 1.1.2 One agreement with all four term kinds, and a counting stub judge
  - [x] 1.1.3 Reports peak RSS, the time per phase, the items or lines judged, and the queries issued
  - [x] 1.1.4 Runs only against a database URL passed on the command line
- [x] 1.2 Run it on today's code at 100k lines (1M will not finish), and record the baseline in `design.md`. The user supplies the database

## 2. Schema (web-api)

- [x] 2.1 Models:
  - [x] 2.1.1 `changed_at` on `InvoiceLine` and `Invoice`, stamped by a change-tracking mapper event for the fields a check reads
  - [x] 2.1.2 `item_key` on `InvoiceLine`
  - [x] 2.1.3 `analysed_from` and `full_analysis` on `Agreement`
  - [x] 2.1.4 A new `AgreementTermSpend` model in its own file
- [x] 2.2 Migration `0022_scalable_agreement_analysis`, with backfills and indexes per the design's migration plan. Don't run it
- [x] 2.3 Audit raw `text()` / string SQL updates of `invoice_lines` and `invoices`, and convert any to Core `update()` so `onupdate` fires (with a test for one converted path, if any)
- [x] 2.4 Tests: `changed_at` moves on a category or invoice supplier change, and not for an emission sector, a bulk update of other fields, or an unchanged value

## 3. Items (ai-api `items/`)

- [x] 3.1 `items/keys.py`: `item_key(item_name, description, unit, category_id, vendor_id)`, normalised (tests: case and spacing collide; supplier and category separate)
- [x] 3.2 `items/refresh.py`: compute `item_key` page by page for lines whose key is null or that changed since a timestamp, joined to their invoice's vendor; bulk update, commit per page (tests: a backfill; only changed lines touched; an invoice vendor change rekeys its lines)
- [x] 3.3 `items/grouping.py`: items as SQL aggregates (key, text, category, vendor, line count, spend, first and last date), filtered by company, date range and category ids (tests on SQLite)
- [x] 3.4 `items/index.py`, the Qdrant collection per company:
  - [x] 3.4.1 Ensure the collection, and embed the missing items in batches
  - [x] 3.4.2 Update the date payload
  - [x] 3.4.3 `search(text, categories?, overlapping dates, threshold, limit)`
  - [x] 3.4.4 Raise `SimilarityUnavailable` on connection errors
  - [x] 3.4.5 Tests with Qdrant's in-memory client and the bag-of-words embedder

## 4. Judging per item (ai-api `compliance/judge/`)

- [x] 4.1 A batched prompt and reply model: numbered items, and a JSON list back, sharing the per-item wording with `judge_prompt`
- [x] 4.2 `Judge.judge_items(term, items)`:
  - [x] 4.2.1 One `IN` lookup per batch of keys
  - [x] 4.2.2 Ask the misses in batches of `AGREEMENT_JUDGE_BATCH` on a `ThreadPoolExecutor(AGREEMENT_JUDGE_CONCURRENCY)`
  - [x] 4.2.3 Re-ask a failed or incomplete batch one item at a time
  - [x] 4.2.4 Store on the run's session
  - [x] 4.2.5 Count judged, cached and unjudged
- [x] 4.3 `JUDGE_VERSION = 3`. Judgements are keyed by `item_key` in `question_key`
- [x] 4.4 Tests:
  - [x] 4.4.1 12,000 identical lines are one question (a run-level test, done with 5.7)
  - [x] 4.4.2 A cached item isn't asked
  - [x] 4.4.3 A malformed batch falls back to single items
  - [x] 4.4.4 A missing item in a batch reply is re-asked
  - [x] 4.4.5 Concurrency doesn't lose answers

## 5. Candidates and incremental runs (ai-api `compliance/`)

- [x] 5.1 `candidates.py`, rewritten:
  - [x] 5.1.1 Category items in SQL, with descendants and the suggested categories for terms without any
  - [x] 5.1.2 Union with the index search
  - [x] 5.1.3 Order by spend, and cap at `AGREEMENT_CANDIDATES_MAX` (default 5,000), reporting a cap
  - [x] 5.1.4 Tests: category only when Qdrant is down; the cap; similarity hits outside the categories
- [x] 5.2 `scope.py`: decide full or incremental per agreement and term, from `analysed_from`, `full_analysis` (also set by header edits of validity, supplier or currency) and `agreement_terms.updated_at` (tests for each trigger)
- [x] 5.3 `pages.py`: keyset pages of in-scope lines per term, via the judgement join, within the validity, minus ruled-out lines, and restricted to changed lines when incremental (tests: page boundaries; ruled-out excluded; only changed lines)
- [x] 5.4 `findings.py`, the per-page work:
  - [x] 5.4.1 Prefetch FX, then evaluate the rules
  - [x] 5.4.2 Upsert and prune the findings of the page's lines, keeping reviews; commit
  - [x] 5.4.3 Remove `compliant` drafts for preferred-supplier and commitment terms
- [x] 5.5 `totals.py`: recompute `agreement_term_spend` per term and touched month with one SQL aggregation, split by from-supplier (identity by vendor or international VAT) (tests: deletion-safe recompute; a flipped judgement)
- [x] 5.6 `run.py`, rewritten:
  - [x] 5.6.1 Per agreement: refresh keys, then index, then candidates, then judge, then pages, then totals
  - [x] 5.6.2 Move `analysed_from` to the run's start and clear `full_analysis` at the end
  - [x] 5.6.3 Produce the new summary
- [x] 5.7 Tests:
  - [x] 5.7.1 An incremental run after a sync touches only new lines
  - [x] 5.7.2 A recategorized line is redone
  - [x] 5.7.3 An edited term redoes all its lines
  - [x] 5.7.4 A crash mid-run (an exception injected after page 2) leaves the watermark, and the rerun doesn't duplicate
  - [x] 5.7.5 The existing rule scenarios still hold
- [x] 5.8 Config and `.env.example`: `AGREEMENT_JUDGE_BATCH`, `AGREEMENT_JUDGE_CONCURRENCY`, `AGREEMENT_PAGE_SIZE`, and the new cap default

## 6. API and report (web-api)

- [x] 6.1 `POST /companies/{id}/agreements/analyse?full=true` sets `full_analysis` on the company's active agreements; the sync's replace path does too (tests)
- [x] 6.2 The report's spend in scope, supplier share and commitment progress come from `agreement_term_spend` (tests; the existing report tests keep passing)
- [x] 6.3 The report carries `capped_terms` and `similarity_available` from the agreement's last summary
- [ ] 6.4 Check the report and dashboard queries with `EXPLAIN` on the benchmark database, adding indexes where they scan lines

## 7. Web

- [x] 7.1 A **Check everything again** action beside **Check again**, for managers, calling the full run (test)
- [x] 7.2 Show a capped term's note ("only the 5,000 largest items were checked") and "similarity unavailable" on the report (tests)
- [x] 7.3 The "Everything" view and its copy no longer imply per-line compliant rows for supplier and commitment terms

## 8. Verification

- [ ] 8.1 Run the web-api, ai-api and web suites
- [ ] 8.2 Rerun the benchmark at 1,000,000 lines (full and incremental) and record peak RSS, wall time and items judged against the baseline in `design.md`
- [ ] 8.3 A real-model sample: 200 items, batched against single. Keep `AGREEMENT_JUDGE_BATCH` only if accuracy is within 2 points
- [ ] 8.4 With the user's go-ahead: run migration 0022 on dev, analyse the test agreement in full, and check that the report matches what it showed before (except the removed compliant rows)
