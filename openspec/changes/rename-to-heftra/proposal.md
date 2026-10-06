## Why

The product cannot launch as **Steelyard**: `steelyard.com` and the useful
alternatives are taken. It is now **Heftra**. The owner has bought `heftra.com`
and `heftra.ai`, and has replaced the logo pack in `brand/`. The mark
("Counterweight"), the palette, the favicons and the tagline are unchanged. Only
the wordmark and the OG image changed. Until the code catches up, the app, the
landing site, the infrastructure and the GitHub repository all carry a name the
company cannot use.

## What Changes

- **The product is named Heftra everywhere a person reads a name.** This covers:
  - the web app (browser title, manifest, `PRODUCT_NAME`, the "Steelyard AI"
    actor in voucher activity);
  - the landing site (copy, legal pages, metadata, `llms.txt`, manifest, 404);
  - the FastAPI and Streamlit titles, module docstrings and `alembic.ini`;
  - README, the app READMEs, `openspec/config.yaml` and the living specs.
- **The lockup is re-copied from the new pack.** The `Logo` component (web) and
  `Lockup.astro` (landing) take their wordmark paths and viewBox from
  `brand/svg/heftra-lockup-black.svg`. The symbol geometry is byte-identical and
  stays. `og-image-1200x630.png` is re-copied into both apps' `public/`.
- **The site lives on `heftra.com`.**
  - `https://heftra.com` is canonical, with the app at `app.heftra.com` and the
    API at `api.heftra.com`.
  - `heftra.ai`, `www.heftra.ai` and `www.heftra.com` 301-redirect to it.
  - Contact addresses become `hello@heftra.com` and `privacy@heftra.com`.
  - The landing Dockerfile and compose defaults, `.env.example`, deploy docs
    and the CORS example move with it.
  - `brand/README.md` already uses `https://heftra.com` for the OG image and
    stays as the owner wrote it.
- **BREAKING (infra):** the compose project, the PostgreSQL database, role and
  password, and the default S3 bucket and dev credentials all go from
  `steelyard` to `heftra`. The landing compose project becomes
  `heftra-landing`.
  - `scripts/rename-dev-db.sh` defaults to `steelyard → heftra`.
  - Because the compose project name prefixes the named volume `rustfs_data`,
    a one-time step carries uploaded files across.
  - Every developer's `.env` `DATABASE_URL` changes.
- **BREAKING (landing):** the theme storage key `steelyard-theme` becomes
  `heftra-theme`. A visitor's stored theme choice resets once. The site has not
  launched yet, so this costs nothing real.
- **The repository is renamed.**
  - The GitHub repo goes from `HadiSDev/steelyard` to `HadiSDev/heftra`, and
    `origin` is updated. GitHub keeps a redirect from the old URL.
  - The local folder goes from `~/repos/spend-predictor-rag` to `~/repos/heftra`.
    That move also moves git worktree paths and the Claude Code project memory,
    so the owner does it, following a written runbook, after the code change
    lands.
- **Not renamed:** the package names (`web-api`, `ai-api`, `mock-erp`,
  `landing`, `frontend`), Python modules, the "Counterweight" mark name, the
  tagline, archived openspec changes and `docs/superpowers` history.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `brand-identity`: the product name requirement becomes "Heftra", with
  "Steelyard" added to the legacy names that must not appear. The infrastructure
  requirement moves to `heftra` and covers carrying an existing `steelyard`
  database and object store across. Logo, metadata and manifest scenarios name
  Heftra.
- `frontend-ui-library`: the theming requirement is renamed from "the Steelyard
  palette" to "the Heftra palette". Its behaviour is unchanged.

The `landing-site` and `demo-requests` capabilities are still in the open
`landing-site` change and have no living spec yet. Their delta specs there are
edited in place to name Heftra and `heftra.com`, so they archive correctly.

## Impact

- **`apps/web`**: `brand-head.ts`, `public/manifest.json`, `public/og-image`,
  `components/brand/logo.tsx` (wordmark path and viewBox),
  `describe-event.ts`, the loading-screen docstring, the README, and the tests
  that assert the name or read `brand/svg/steelyard-*`.
- **`apps/landing`**:
  - code and content: `site.ts`, content YAML, the sections, pages, legal text,
    `Lockup.astro`/`Symbol.astro`/`Header.astro` labels, `theme.ts`,
    `site.webmanifest`, `public/og-image`;
  - deploy: Dockerfile, `docker-compose.yml`, `.env.example`, the README;
  - tests: unit, build and e2e fixtures;
  - screenshots: the five product captures show the web app's sidebar lockup,
    so they are recaptured once the web app is renamed.
- **`apps/web-api`, `apps/ai-api`**: titles, docstrings, `config.py` and
  `db/session.py` defaults, `alembic.ini`, test fixtures naming the bucket.
- **Infra**: root `docker-compose.yml`, `.env.example`, `scripts/rename-dev-db.sh`.
  Dev data needs one-time steps from the owner: rename the database, copy the
  RustFS volume, update `.env`. Agents do not run these against the live stack.
- **External, done by the owner**:
  - **GitHub**: the repo rename. An agent runs it only after explicit
    confirmation.
  - **Cloudflare**: DNS and tunnel hostnames, plus the `heftra.ai` redirect
    rule.
  - **Email**: mailboxes for `hello@` and `privacy@heftra.com`.
  - **Clerk**: the application name and allowed origins for `app.heftra.com`.
- **Claude Code memory**: the project memory directory is keyed by the folder
  path, so it is copied to the new key when the folder moves. Memory entries
  that mention Steelyard are updated.
