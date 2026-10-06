# Demo company: Nordlys Byg A/S

Seeds a **fictional** Danish general contractor into the local dev database so every page of the
web app has full, believable data for screenshots. Nothing here is real: the company's VAT number
(DK40012345) and every supplier's fail the Danish CVR checksum, and all websites are on the
reserved `.example` domain.

It lives in `ai-api` because it builds the stored items with the app's own
`ai_api.items.stored.refresh_company_items`. No LLM is called.

## Commands

Run from the repository root (the database comes from `DATABASE_URL` in the root `.env`):

```bash
uv run python apps/ai-api/scripts/demo_company            # seed, replacing any earlier demo rows
uv run python apps/ai-api/scripts/demo_company --reset    # also delete and rewrite its suppliers
uv run python apps/ai-api/scripts/demo_company --remove   # delete the demo company and stop
```

`--no-fx-warm` skips filling the shared ECB rate cache for the seeded days; `--no-report` skips
reading the company back through the app's report functions.

Every row has a fixed id, so a re-run deletes the demo company's rows (with the app's own
`delete_company`) and writes the same ones again. It never touches another company's rows: the
command counts every other company's rows before and after and exits non-zero if any changed.

## What it writes

- The company in organization `35156cc7-…`, with its own spend tree (Direct / Indirect, 32
  leaves), a connected mock ERP with expense, VAT and payables accounts, and 35 fictional
  suppliers in the shared supplier table, described as enrichment would.
- Two years of purchases, October 2024 to September 2026, in EUR: about 1,800 invoices and
  3,700 categorized lines with emission sectors, and the vouchers' postings the dashboard reads.
  The spend follows the building season, grows year on year and has a few stage-payment spikes.
- Stored items with specifications, and 15 open alternatives (history, benchmark, marketplace).
- Two active framework agreements with confirmed terms, their PDFs in the file store, findings
  for every in-scope line and the terms' monthly spend.
- Finished pipeline runs, so the worker treats the company as up to date.

## Keeping the worker off it

- `researched_at` is set, so company research skips it.
- Invoices have no documents (`doc_status = not_applicable`), so no document is read.
- Every item has a specification and non-service items are marked searched, so a scan reads and
  searches nothing for `ALTERNATIVES_RESCAN_DAYS` (30 days). A scan run is recorded at seeding,
  so the next automatic scan is a day later and only refreshes the items' figures.
- Agreement analysis is only queued after a sync, document read or categorization, or on request.

After 30 days a running worker searches the items again and may replace the seeded alternatives;
re-run the seed to restore them.
