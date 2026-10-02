## Why

Agreement analysis works for a company with a few hundred lines. It doesn't scale to a company with millions. Each run:
- loads every line in an agreement's validity into memory;
- embeds every line again;
- scores every line against every term in Python;
- asks the model about every candidate line, one at a time, with no cap on lines found by category;
- writes everything in one transaction at the end.

At a million lines that means several GB of memory, minutes of embedding on every run even when nothing changed, and days of model calls on the first run. A crash near the end loses the whole run. Steelyard's mid-market customers sync years of ERP history, so the feature has to work at their size before it ships to them.

## What Changes

- **Judge distinct items, not lines.** Lines are grouped in the database by what they bought: item, description, unit, category and supplier. The scope judge is asked once per item and term, and the answer applies to every line of the item. Model work then grows with the variety of what a company buys, not its volume. Several items can be asked in one prompt, and prompts run concurrently.
- **Incremental runs.**
  - Invoice lines and invoices gain a `changed_at`, stamped by the ORM when something an agreement check reads changes (the item, amounts, category; the invoice's supplier, date, currency), and not for unrelated writes such as emission sectors.
  - A run checks only the lines added or changed since the agreement's last completed run, plus every line of a term that was confirmed or edited since then.
  - A full run happens the first time, and on request.
- **A persistent index of what was bought.** Each distinct item is embedded once and stored in Qdrant per company, with its category and supplier. The similarity route of candidate selection becomes a filtered vector search; nothing is embedded or scored in Python per run.
- **Filtering in the database, work in batches.**
  - Validity, category and item filters run in SQL.
  - In-scope lines are read in keyset pages.
  - Findings are written and committed per batch, so a crash loses at most one batch and the next run resumes.
  - A cap per term keeps runaway scopes bounded and is reported.
- **Commitment spend as totals, not rows.** In-scope spend with and without the supplier is kept as totals per term and month.
  - **BREAKING:** Per-line `compliant` findings are no longer stored for preferred-supplier and volume-commitment terms, where they only said "bought from the supplier". The report's spend in scope, its share with the supplier, and commitment progress are read from the totals.
  - Compliant findings remain for agreed-price and discount checks, where a check was actually made.
- **Measured, not estimated.** A synthetic company with a million varied lines is generated, using the existing deterministic synthetic data. Before and after are benchmarked for memory, wall time and model calls.

## Capabilities

### New Capabilities
- `spend-item-index`: what a company buys as distinct items. They are grouped from its invoice lines, embedded once, and stored in Qdrant per company, with the lines each item covers. They can be searched by similarity with category and supplier filters.

### Modified Capabilities
- `agreement-compliance`, defined by the active `trade-agreements` change, which must be archived first:
  - candidates are distinct items, found by category in SQL and by similarity in the item index, with a cap per term;
  - the judge answers per item, batched and concurrently;
  - runs are incremental with a resumable, batched write;
  - the run summary counts items, lines and batches;
  - commitment progress and spend in scope come from per-term monthly totals;
  - compliant findings are kept only for price and discount checks.

## Impact

- **Migrations:**
  - `changed_at` on `invoice_lines` and `invoices`, backfilled from `created_at`;
  - `item_key` on `invoice_lines`, with indexes for grouping and change scans;
  - an analysis watermark and a full-run flag on `agreements`;
  - an `agreement_term_spend` totals table.
  - Scope judgements keep their table, keyed by item instead of by line question; earlier answers are asked once more.
- **ai-api:**
  - `compliance/` is restructured:
    - candidates move to SQL and Qdrant;
    - the judge works per item with batching and concurrency;
    - the run becomes incremental with batched writes;
  - a new `items/` (or `rag/`) module for the item index;
  - the worker runs analysis in batches.
- **web-api:**
  - report and dashboard queries read the totals for spend in scope and commitments;
  - the request endpoint gains a full-run option.
- **web:**
  - the report reads the same fields;
  - the "Everything" view no longer lists per-line compliant rows for preferred-supplier and commitment terms;
  - a **Check everything again** action for a full run.
- **Infrastructure:** Qdrant gains one collection per company. Postgres needs no extension.
- **Dependency order:** archive `trade-agreements` before applying, so `agreement-compliance` exists in `openspec/specs/`.
