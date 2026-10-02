## Context

`analyse_agreements` (ai-api `compliance/run.py`) runs per company. For each active agreement and confirmed term it does the following:

1. **Load:** `load_lines` reads every positive line in the validity into `AnalysedLine` objects.
2. **Embed:** `LineVectors` embeds them all.
3. **Pick candidates:** `candidates()` takes:
   - every line in the term's categories, with no cap;
   - plus the top `AGREEMENT_CANDIDATES_MAX` by cosine similarity, scored in Python.
4. **Judge:** `Judge.judge` asks the model per line, sequentially, with one cache lookup per line by `(term_id, term_key, question_key)`.
5. **Apply rules:** `rules.evaluate` produces drafts, including a `compliant` row for every in-scope line from the supplier and every commitment line.
6. **Store:** `store_findings` upserts everything, with one `commit()` at the end.

This is fine for the 80-line dev company and doesn't scale; see the proposal. There are also constraints:
- **Tests run on in-memory SQLite.** Production runs on Postgres 16 without extensions.
- **Qdrant is already deployed** (the categorization tree index).
- **The local model is gemma-4-E4B on vLLM.** Replies must be prompted as JSON and parsed, not produced by guided decoding (see the project memory on vLLM guided decoding).
- **Invoice lines and invoices have no `updated_at`.** Lines are written by:
  - the sync runner;
  - the document reader;
  - categorization;
  - manual corrections;
  - tree reassignment (a bulk Core `update()`).

## Goals / Non-Goals

**Goals:**
- **Bounded memory** at any company size. Nothing proportional to the number of lines is held in Python.
- **Model calls proportional to distinct items × terms**, paid once, and then only for new items.
- **Incremental runs** after a sync cost roughly the lines it brought.
- **Crash-safe:** committed work is kept, and a rerun doesn't duplicate.
- **Measured:** a reproducible million-line benchmark, before and after.

**Non-Goals:**
- Sharding analysis across several workers. One worker per company is enough once runs are incremental.
- Changing the rules themselves: amounts, tolerances, kinds.
- Real-time analysis on every line write.
- Moving vectors into Postgres (pgvector).

## Decisions

### 1. Items: a persisted `item_key` on each line, refreshed by analysis

`invoice_lines.item_key` is a SHA-256 of the normalised item name, description, unit, `spend_category_id` and the invoice's `vendor_id`. Normalised means lower case with collapsed spaces.

- **Computing it:** the key is computed in Python, page by page, for lines whose key is null or that changed since the agreement's watermark. Changed means the line's or its invoice's `updated_at` is later. This step runs at the start of each analysis. The first run backfills.
- **Grouping:** items are then a `GROUP BY item_key` in SQL, with count, spend sum and min/max date, using an index on `(company_id, item_key)`.

*Alternatives considered:*
- **A SQL expression grouped on the fly** (`md5(lower(trim(...)) || ...)`). It can't be indexed, because the vendor lives on the invoice. It also needs an `md5` shim for SQLite tests.
- **ORM event listeners keeping `item_key` current.** These miss bulk Core updates such as tree reassignment, and miss vendor changes made on the invoice.
- **Not storing a key** and filtering lines by the raw tuple. That turns "lines of these items" into very large OR-lists.

Refreshing inside analysis keeps one owner for the key. Its freshness then rides on the same change detection as incremental runs.

### 2. Change detection: `updated_at` on lines and invoices

- **The columns:** `updated_at` with `server_default=now()` and `onupdate=func.now()` on both models. It's backfilled from `created_at`.
- **What it covers:** SQLAlchemy applies column `onupdate` to ORM flushes and to Core `update()` statements that don't set the column. That covers the sync, reader, categorization, corrections and tree reassignment.
- **What it misses:** raw `text()` updates don't fire it. A task audits the codebase for them and converts any it finds.
- **Indexes:** `(company_id, updated_at)` on both tables.

### 3. Watermark and full runs on the agreement

`agreements` gains:
- `analysed_from`, when the last complete run *started*;
- `full_analysis` (bool), set when a full run is requested.

Starting the watermark at the run's start, not its end, means lines changed during a run are picked up by the next one.

A run is full when any of these hold:
- `analysed_from` is null;
- `full_analysis` is set;
- the validity, supplier or currency changed since the watermark (tracked by `agreements.updated_at`);
- a sync replaced data, in which case the replace path sets `full_analysis`.

Per term, the lines to redo are:
- **for a term edited or confirmed since the watermark** (`agreement_terms.updated_at`): all its candidate lines;
- **otherwise:** only its candidate lines that changed.

`POST …/agreements/analyse?full=true` sets `full_analysis` on the company's active agreements.

*Alternative:* a run-level parameter on `pipeline_runs`. That needs a new column and per-kind options for one flag. Keeping the flag on the agreement also survives a crashed run.

### 4. The item index in Qdrant

- **Collection:** `spend_items_{company_id}`, cosine, all-MiniLM-L6-v2 (384 dimensions).
- **Points:** id = `uuid5(item_key)`. The payload holds `item_key`, `category_id`, `vendor_id`, `first_on` and `last_on`.
- **Text:** the item text plus its category path.
- **Indexing:** before candidate selection, items not yet in the collection are embedded in batches of 256. "Not yet in it" is found with a scroll on ids, or tracked with an `indexed` marker table if scrolls prove slow; the benchmark decides. Dates are refreshed with payload-only updates when an item gains lines.
- **Search:** per term, a `query_points` call with a filter on the date range overlapping the validity. Results above `AGREEMENT_SIMILARITY_MIN`, up to the cap.
- **When Qdrant fails:** `SimilarityUnavailable`. The run goes on by category and records `similarity: false`.

*Alternative:* keep Python cosine over an in-memory matrix of items, not lines. That's cheaper than today, but still linear in items per term, and items can reach the hundreds of thousands. Qdrant is already deployed and in use.

### 5. Candidates, the cap and judging per item

- **Candidates:** category candidates come from SQL: items whose `category_id` is in the term's categories, or the suggested ones, with their descendants, and with lines in the validity. They're unioned with the similarity hits and ordered by spend, descending, then capped at `AGREEMENT_CANDIDATES_MAX`, which defaults to 5,000. A capped term is reported.
- **Lines ruled out by a manager** stay per line (`not_in_scope`), applied when findings are written.
- **Batching:** `Judge` takes a list of items. For each, it looks up a stored judgement with one `IN` query per batch of keys, using `(term_id, term_key, question_key=item_key)`.
- **Asking:** misses are sent in prompts of `AGREEMENT_JUDGE_BATCH` items (default 8), each numbered. The reply is a JSON list of `{n, in_scope, same_item, units_comparable, confidence, reason}`.
- **Running prompts:** they run in a `ThreadPoolExecutor(AGREEMENT_JUDGE_CONCURRENCY)` (default 4). Model calls are thread-safe HTTP; DB writes stay on the run's thread.
- **When a batch fails:** a reply that can't be parsed, or one missing items, sends those items again one by one. An item that still fails is unjudged.
- **The prompt:** the per-item wording is shared with the single-item prompt, so the instructions about definitions and the buyer stay identical.
- **Versioning:** `JUDGE_VERSION` is bumped to 3, since keys move from line questions to items.

### 6. Findings and totals, page by page

For each term, in-scope lines are read with keyset pagination over `(invoice_date, id)`, `AGREEMENT_PAGE_SIZE` (default 2,000) at a time. The query is:
- `invoice_lines` joined to `agreement_scope_judgements` on `item_key`;
- filtered on the term, the current key and `in_scope`;
- within the validity;
- minus ruled-out lines;
- restricted to changed lines when incremental.

Per page:
1. Prefetch FX for the page's dates.
2. Evaluate the rules.
3. Upsert the findings by `(term, line, kind)` and delete the ones the page's lines no longer produce. Reviews are kept.
4. Commit.

**Totals:** `agreement_term_spend(term_id, month, from_supplier, amount, lines)` is recomputed with one SQL aggregation per term and touched month, as lines × in-scope judgements. A full run touches every month. Recomputing from source rather than applying deltas means a crashed run, a deleted line or a judgement that flipped can't leave totals drifting. The touched months of an incremental run are those of its changed lines, plus all months of a term whose judgements changed.

The `compliant` per-line rows of preferred-supplier and commitment terms disappear. The first full run deletes them as "no longer produced".

### 7. The run summary and batching the worker

The summary reports, per run:
- agreements, terms, full or incremental per agreement;
- items: candidates, judged, cached, unjudged;
- capped terms;
- lines read and pages written;
- findings by kind;
- whether similarity was available.

A run commits after every page, so a long first run is interruptible and the worker's stale-run recovery still applies. The watermark moves only at the agreement's end.

### 8. Benchmark

`apps/ai-api/scripts/agreement_benchmark.py`, not part of `pytest`:
- builds a synthetic company from the existing deterministic synthetic catalog: N lines (default 1,000,000), around 20,000 distinct items, 40 suppliers, 3 years;
- adds one agreement with the four term kinds;
- runs analysis with a counting stub judge;
- reports peak RSS, wall time per phase, the items judged and the queries issued;
- runs a second, incremental pass after adding 5,000 lines;
- runs against a Postgres database the user names. It never touches the dev database unless told to.

## Risks / Trade-offs

- **[Batched prompts lower the small model's accuracy]** → Batch size is configurable and defaults to 8. The benchmark includes a real-model sample of 200 items, scored batched against single and compared against the stub's ground truth. Batching is set to 1 if accuracy drops by more than 2 points.
- **[A raw SQL update elsewhere skips `updated_at`, so a changed line is never rechecked]** → A task audits `text(` updates. A full run is offered in the UI and runs on agreement changes and replaces. A nightly full run is left as an open question.
- **[Qdrant and Postgres drift (a dropped collection)]** → Items missing from the collection are re-embedded on the next run. A collection that disappears is rebuilt from the items in Postgres.
- **[The cap hides real rule breaks in a very broad term]** → The cap is high by default and ordered by spend, and a capped term is reported in the summary and on the report ("only the 5,000 largest items were checked"), so it's visible.
- **[The first run on a big company takes long]** → It's batched, resumable and reports progress in its summary. Model calls are bounded by distinct items, which is the real cost.
- **[Dropping per-line compliant rows loses the green rows in "Everything"]** → Price and discount checks keep theirs. The supplier share and commitment progress show the supplier's spend.

## Migration Plan

1. **Migration `0022_scalable_agreement_analysis`:**
   - `updated_at` on `invoice_lines` and `invoices`, backfilled from `created_at`;
   - `item_key` on `invoice_lines`;
   - indexes `(company_id, item_key)`, `(company_id, updated_at)` and `invoices (company_id, updated_at)`;
   - `agreements.analysed_from` and `full_analysis`, with `full_analysis` set true for existing agreements;
   - `agreements.updated_at` if it's missing;
   - the `agreement_term_spend` table.
2. **Deploy the API and worker.** The first run per agreement is full: it backfills item keys, builds the index, re-judges with v3 keys and replaces compliant rows with totals.
3. **Rollback:** the downgrade drops the new columns and table. The previous code ignores them. Stale v3 judgements are harmless, because they have different keys.

## Open Questions

- **A scheduled weekly full run as a safety net** against missed `updated_at`s, or only on demand? Default: on demand plus the automatic triggers.
- **Default `AGREEMENT_CANDIDATES_MAX` (5,000) and `AGREEMENT_JUDGE_BATCH` (8):** the benchmark settles them.
- **Should the item key ignore the supplier for the scope judge** (one answer per product across suppliers)? It would cut calls further, but the judge sees the supplier today. Left out for now.
