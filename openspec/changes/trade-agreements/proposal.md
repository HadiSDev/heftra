## Why

Customers sign trade and framework agreements with suppliers. The terms decide what the company should pay and where it should buy, for example:
- "IT equipment is bought from us when we have it in stock."
- "ThinkPad T14 at DKK 8,000."
- "10% off accessories."
- "At least DKK 500,000 a year."

Nobody checks the spend against these terms. Employees buy laptops from a webshop instead of the framework supplier, the supplier invoices above the agreed price, and discounts quietly go unapplied. Steelyard already has every invoice line with its supplier, item, quantity, unit price and category. What's missing is the agreements themselves, and a way to read spend against them.

Rule breaks matter most: buying in-scope goods from another supplier when an agreement says otherwise. These must be easy to find, explain and act on.

## What Changes

- **File storage:** an S3-compatible object store. Locally this is **RustFS** in docker compose; any S3 service works in production. It sits behind a small `FileStore` interface in web-api, which ai-api reuses. It is the first place the app keeps uploaded bytes.
- **Agreements:**
  - Managers upload an agreement PDF for a company. It is stored, and the worker reads it: pdfplumber text first, falling back to vision for scanned pages, following the invoice reader.
  - The LLM drafts the agreement's header: supplier, reference, validity period and currency.
  - It also drafts its **terms**, each with the clause it came from (quoted, with its page). Four kinds:
    - **preferred supplier**: a scope that must be bought from this supplier, with any condition such as "when in stock";
    - **agreed price**: an item at a unit price;
    - **discount**: a percentage on a scope;
    - **volume commitment**: an amount over a period, optionally with rebate tiers.
  - A manager reviews the drafts next to the document: edits, confirms or rejects each term, adds missing ones, and links the supplier to a known supplier. Only confirmed terms are analysed.
- **Compliance analysis:** a new pipeline run kind, `analyse_agreements`.
  1. For each confirmed term, retrieve candidate lines within the agreement's validity: spend category first, then embedding similarity to the term's scope or item.
  2. An LLM judges whether each candidate is in scope, and for agreed prices, whether it is the priced item. Its answers are cached.
  3. Findings are calculated deterministically and stored:
     - **off-contract purchase (rule break):** in-scope spend with another supplier;
     - **overcharge:** the agreed item invoiced above its agreed price;
     - **missed discount:** in-scope lines from the supplier without the discount;
     - **potential saving:** the agreed price or discount applied to spend elsewhere;
     - **commitment progress:** for volume commitments.
  4. The run happens when terms are confirmed, after sync or document reading adds lines, and on request.
- **Reviewing findings:** a manager can mark a finding as an accepted exception (e.g. "out of stock that week") or as not in scope, with a note. That decision survives later analysis runs.
- **Web:**
  - An **Agreements** page in the main navigation: the list of agreements with their rule breaks and amounts, and upload with the existing `FileDropzone`.
  - An agreement detail page:
    - the document beside its terms for review;
    - after confirmation, a report with summary figures, a **Rule breaks** table, price and discount checks, and commitment progress. Each finding opens its voucher in the existing voucher drawer.
  - A dashboard section: the period's rule breaks and off-contract spend, linked to Agreements.

## Capabilities

### New Capabilities
- `file-storage`: storing and reading uploaded files in an S3-compatible bucket (RustFS locally), behind one interface.
- `trade-agreements`: uploading, storing, reading and extracting agreements and their terms, and the review that confirms them.
- `agreement-compliance`: analysing a company's spend lines against confirmed terms, the findings it stores, and reviewing those findings.
- `frontend-agreements`: the Agreements list, upload, term review and compliance report.

### Modified Capabilities
- `pipeline-runs`: a new run kind, `analyse_agreements`, requested automatically and by managers of the company. The worker also reads pending agreements on its own, as it does documents.
- `frontend-auth-dashboard`: the navigation gains **Agreements**.
- `frontend-dashboard`: a contract compliance section with the period's rule breaks.

## Impact

- **Infrastructure:**
  - a `rustfs` service in `docker-compose.yml`, on host ports 9100 (S3) and 9101 (console), with a volume;
  - S3 settings in `.env.example`;
  - a bucket created at startup.
- **Dependencies:**
  - `boto3` in web-api, which ai-api inherits through the workspace. The user runs the sync.
  - The existing `pdfplumber`, `pypdfium2`, CrewAI and Qdrant cover the rest.
- **web-api:**
  - new `storage/`, `agreements/` and `compliance/` packages;
  - models `Agreement`, `AgreementTerm` and `AgreementFinding`, plus `File` rows for uploads (a new `file_type`), in migration `0020_trade_agreements`;
  - routers for agreements, terms, findings and the file stream;
  - a new `PipelineRunKind`.
- **ai-api:**
  - `agreements/` for reading and term extraction, and `compliance/` for retrieval, the scope judge and the analysis run;
  - worker changes to read pending agreements and to queue analysis after sync and document reading.
- **web:**
  - `routes/_authed/agreements/` (list and `$agreementId`);
  - `components/agreements/`;
  - API types and queries;
  - a new nav entry;
  - a dashboard section.
- **Out of scope:**
  - attributing a rule break to the employee who bought it (nothing in the ERP data says who did);
  - Word or other non-PDF formats;
  - e-mail or notification alerts;
  - supplier stock availability (the "when in stock" condition is shown, not verified);
  - negotiating or recommending new agreements.
