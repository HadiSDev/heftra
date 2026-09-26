## Why

Steelyard knows what a company spent and on what, but not what that spend cost the climate. Purchased goods and services (Scope 3, category 1) are most of an SMB's footprint, and the standard first estimate is spend-based: posted spend × an emission factor for the sector and country it was bought from. Every Spend Lines voucher already has its net posted spend, its lines, their categories and a supplier with a country, so the estimate is one factor lookup away once each line knows which emission sector it belongs to.

Commercial emission-factor APIs such as Climatiq charge per call and keep the factors behind their service. The open alternatives were compared:

- **Open CEDA (Watershed)**: CC BY-SA, commercial use allowed with attribution, about 400 industries × 149 countries (Denmark included), kgCO₂e per 2023 USD, one downloadable workbook. **Chosen.**
- **EXIOBASE through pymrio**: 3.9 and 3.10 moved to a non-commercial licence (a commercial one must be negotiated). 3.8.2 is still CC BY-SA, but its real data ends in 2011 and each year means a ~250 MB download plus a Leontief inversion. Kept possible as a later factor source, not built now.
- **US EPA Supply Chain GHG factors**: public domain, but they describe the US economy only.

## What Changes

- A store of **emission factor sets**: an imported, versioned dataset (source, version, classification, currency, price year, licence and attribution) with its sectors, a factor per sector and country (converted to purchaser prices), and regional averages for countries without their own. There is one active set at a time, and an importer CLI reads the Open CEDA workbook into it.
- **Emission sector matching** in ai-api: each invoice line is matched to one sector of the active set's classification by an AI agent. The agent has tools to search the sectors (Qdrant over names and descriptions), read a sector's description, read the supplier's profile, and read the invoice's other lines. When the agent fails, a single-shot choice from the 12 closest sectors is made instead. A low-confidence match is kept as a suggestion and marked for review. The match reads the line's text, its spend category, and the supplier's name, description and country. Results are cached; a human's choice is never overwritten. It runs as a new pipeline run kind and a CLI.
- **Spend emissions** in web-api: a voucher's net posted spend is split across its lines by their share (the same netting Spend Lines and the dashboard use), converted to the factor's currency at the voucher date, and multiplied by the factor for the line's sector in the supplier's country (falling back to the company's country). Nothing is stored: it is computed on read, so corrections show at once. Anything that can't be estimated is counted with its reason.
- **API**:
  - The voucher list gains each voucher's and each line's kgCO₂e and each line's sector.
  - A new emissions summary follows the Spend Lines filters.
  - A sector search feeds the picker.
  - The line update accepts a sector choice.
- **Spend Lines UI**:
  - An emissions card beside the coverage card, with the total, the share of spend estimated, and the method and attribution.
  - A CO₂e column on vouchers.
  - Each line's sector and CO₂e.
  - A sector picker in the line editor.

## Capabilities

### New Capabilities
- `emission-factors`: importing and storing versioned emission factor sets, their sectors and per-country factors; the active set; factor lookup with country fallback; licence attribution.
- `emission-sector-matching`: matching invoice lines to emission sectors with a tool-using agent and a single-shot fallback, caching, confidence and review, the rule that a human's choice wins, and the CLI.
- `spend-emissions`: computing kgCO₂e for vouchers and lines from posted spend, the summary and sector search endpoints, correcting a line's sector, and reporting what could not be estimated and why.

### Modified Capabilities
- `pipeline-runs`: a new run kind, `match_emissions`, that the worker executes.
- `frontend-settings`: the company Run menu offers **Match emission sectors**.
- `frontend-erp-entries`: Spend Lines shows the emissions card, the voucher and line CO₂e, the line's sector, and a sector picker.

## Impact

- **web-api**:
  - New models and migration `0017`: `emission_factor_sets`, `emission_sectors`, `emission_factors`, plus `InvoiceLine.emission_sector_id`, `emission_sector_source` and `emission_sector_confidence`.
  - New `web_api/emissions/` package: lookup, estimate and importer.
  - Changed: `routers/erp_entries.py` (voucher list fields, summary endpoint), the invoice-line PATCH, and `PipelineRunKind`.
  - New dependency `openpyxl` for reading the workbook; the user installs it.
- **ai-api**:
  - New `ai_api/emissions/` package: sector index, the agent and its tools, the single-shot fallback, and the runner. This is the first CrewAI agent in the repo that uses tools.
  - A new worker executor, `match_emissions`.
  - Reuses `rag/indexer` helpers and the categorization cache pattern.
- **web**: the Spend Lines panel, the voucher table, the line editor, the Settings Run menu labels, and new API types and queries.
- **Data and licence**:
  - The Open CEDA workbook is downloaded by the user from openceda.org and imported once per release.
  - The attribution "CEDA by Watershed" must be shown wherever figures appear.
- **Out of scope:**
  - Dashboard emission tiles.
  - Activity-based factors (kWh, km, kg).
  - Supplier-specific (primary) data.
  - Inflation adjustment to the factor's price year.
  - EXIOBASE and pymrio.
