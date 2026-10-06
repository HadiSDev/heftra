## 1. Preflight

- [x] 1.1 Re-read `git status`. Only the owner's `brand/` changes and untracked `data/agreements/` may be pending. Stop and ask if another agent has uncommitted edits under `apps/`, `docker-compose.yml`, `.env.example` or `scripts/`.
- [x] 1.2 Record baselines:
  - `uv run pytest -q` counts;
  - `./node_modules/.bin/vitest run` counts in `apps/web` and `apps/landing`;
  - a clean `tsc --noEmit` (web) and `astro check` (landing);
  - the full `git grep -ic steelyard` list, saved to the scratchpad.
- [x] 1.3 Stage the owner's `brand/` changes as renames (`git add -A brand/`) so history follows `steelyard-*` → `heftra-*`. `brand/README.md` already points the OG URL at `https://heftra.com` and needs no edit.

## 2. Web app (`apps/web`)

- [x] 2.1 `lib/brand-head.ts` `PRODUCT_NAME` = "Heftra". `public/manifest.json` `name`/`short_name` "Heftra". Re-copy `brand/social/og-image-1200x630.png` to `public/`.
- [x] 2.2 `components/brand/logo.tsx`:
  - copy the wordmark path and viewBox verbatim from `brand/svg/heftra-lockup-black.svg`;
  - `aria-label` and docstrings say "Heftra";
  - recompute any width/height that was derived from the old aspect ratio;
  - keep the symbol geometry.
- [x] 2.3 `entries/voucher/activity/describe-event.ts`: `AI_NAME` "Heftra AI", `SYSTEM_NAME` "Heftra". Update the loading-screen docstring and `apps/web/README.md`.
- [x] 2.4 Update tests that name the product or read `brand/svg/steelyard-*`:
  - `brand.test.ts`, `brand-head.test.ts`, `logo.test.tsx`;
  - `app-shell.test.tsx`, `ui.test.tsx`, `sign-in.test.tsx`;
  - `describe-event.test.ts`, `voucher-activity-tab.test.tsx`.
- [x] 2.5 Add `/steelyard/i` to `RETIRED` in `brand-scan.test.ts`. Run the web vitest suite and `tsc --noEmit`; both match the baseline plus the new assertions.

## 3. Landing site (`apps/landing`)

- [x] 3.1 `src/lib/site.ts`: name "Heftra"; description, `homeTitle` and `homeDescription` reworded where the name sits in a sentence; titles stay ≤ 60 characters and descriptions ≤ 160. `contactEmail` is `hello@heftra.com` and `privacyEmail` is `privacy@heftra.com`.
- [x] 3.2 `Lockup.astro`: wordmark path and viewBox from `heftra-lockup-black.svg`. Labels "Heftra" in `Lockup.astro`, `Symbol.astro` and `Header.astro` ("Heftra home"). Repoint `tests/unit/logo-geometry.test.ts` at `brand/svg/heftra-*.svg`.
- [x] 3.3 Copy and content:
  - content YAML: `features.yaml`, `faq.yaml`;
  - sections: Hero, HowItWorks, Features, Security;
  - `ProductFrame.astro`, `DemoForm.astro`, `LegalPage.astro`, `Footer.astro`;
  - pages: `demo.astro`, `privacy.astro`, `terms.astro`, `404.astro`, `llms.txt.ts`.

  Read each sentence rather than substituting blindly. Bump the legal pages' "Last updated" date.
- [x] 3.4 `src/scripts/theme.ts` storage key `heftra-theme` (no migration of the old key). Also `public/site.webmanifest` name/short_name, and re-copy `og-image-1200x630.png` into `public/`.
- [x] 3.5 Deploy defaults:
  - `Dockerfile` ARGs and the `docker-compose.yml` `PUBLIC_*` defaults → `https://heftra.com`, `https://app.heftra.com`, `https://api.heftra.com`;
  - compose `name: heftra-landing`;
  - `.env.example` production comments;
  - the README: title, origins, the Cloudflare step with the `heftra.ai`/`www` redirect rule, CORS origin, `docker build -t heftra-landing`.
- [x] 3.6 Tests:
  - update the fixtures in `tests/unit/links.test.ts`, `seo.test.ts`, the config test, `tests/build/metadata.test.ts`, `tests/build/seo.test.ts`, `tests/e2e/demo-form.spec.ts` and `fallbacks.spec.ts`;
  - add `steelyard` to the build test's legacy names;
  - add a build test that the whole `dist/` contains no "steelyard" and that every product-domain email ends in `@heftra.com`.
- [x] 3.7 Verify in an isolated scratchpad copy (`mkdir -p`, then rsync with symlinked `node_modules`): `astro check`, `vitest run`, `astro build`, `playwright test`. All pass. If the owner's dev server is running on 3200, tell them to restart it with `.astro` and `node_modules/.vite` cleared.

## 4. Backend and docs

- [x] 4.1 Change "Steelyard" to "Heftra" in:
  - `web_api/app.py` title ("Heftra Web API");
  - `dashboard/app.py` (docstring, `page_title`, `st.title`);
  - the `ai_api/sync/runner.py` docstring;
  - the `alembic.ini` header.
- [x] 4.2 README:
  - the lockup `<picture>` points at `brand/png/heftra-lockup-*-600.png`;
  - title and intro say Heftra;
  - the landing section names `heftra.com`.

  Also update `openspec/config.yaml` context, the CLAUDE.md product and brand mentions if present, `openspec/specs/domain-model/spec.md` Purpose, and the `openspec/specs/brand-identity` Purpose line.
- [x] 4.3 Edit the open `landing-site` change in place:
  - `proposal.md`, `design.md` (origins, contact addresses, CORS origin, deploy note) and `tasks.md` mentions;
  - delta specs `landing-site/spec.md` (CTA targets, canonical URLs, `og:title`, lockup, 404, `llms.txt`) and `brand-identity/spec.md` (header lockup name; add "steelyard" to the legacy-name scenario).

  Run `openspec validate landing-site --strict`.

## 5. Infrastructure

- [x] 5.1 Root `docker-compose.yml`:
  - `name: heftra`;
  - `POSTGRES_DB`/`USER`/`PASSWORD` set to `heftra`;
  - RustFS key defaults `heftra` / `heftra-dev-secret`.
- [x] 5.2 Move to `heftra` / `heftra-dev-secret`:
  - `web_api/config.py`: `DATABASE_URL` and `S3_BUCKET` defaults;
  - `web_api/db/session.py` default;
  - `.env.example`: `DATABASE_URL`, `S3_*`, and `https://heftra.com` in the documented `WEB_API_CORS_ORIGINS`.

  Update `tests/storage/test_storage.py` and the `test_public_demo_requests.py` booking fixture.
- [x] 5.3 `scripts/rename-dev-db.sh`: defaults `FROM=steelyard`, `TO=heftra`, with usage lines for the default, `--from spend_predictor`, and the rollback.
- [x] 5.4 Test the script against a throwaway container: `docker run postgres:16` initialised as `steelyard`, seeded with one table and row.
  - The default run renames the database and role to `heftra` and the row survives.
  - A second run is a no-op.
  - A second throwaway initialised as `spend_predictor` renames with `--from spend_predictor`.

  Remove the containers afterwards.
- [x] 5.5 Test the volume carry-across against throwaway volumes, never `steelyard_rustfs_data`:
  - start `rustfs/rustfs:1.0.0` on a scratch volume with the old credentials, and put one object in bucket `steelyard`;
  - copy the volume with the design's alpine command;
  - start RustFS on the copy with the old credentials, and confirm the object reads back.

  Remove the volumes afterwards.
- [x] 5.6 Document the infra names and carry-over: new names, the migration steps, and that `POSTGRES_*` only applies to a fresh `pgdata/`. CLAUDE.md has no infra note, so this goes in the README Setup section. Never run the migration against the owner's stack, and never edit any `.env` (root, apps or worktrees).

## 6. Owner runbook

- [x] 6.1 Write `openspec/changes/rename-to-heftra/runbook.md` with copy-pasteable steps in order:
  1. Stop sessions and dev servers.
  2. `docker compose -p steelyard down`.
  3. `mv` the folder and run `git worktree repair`.
  4. Copy `~/.claude/projects/-home-hadi-repos-spend-predictor-rag` to `-home-hadi-repos-heftra`.
  5. Rebuild the `.venv`s (`uv sync`) and reinstall `node_modules` only if bins break.
  6. `docker compose up -d postgres`, then `scripts/rename-dev-db.sh`.
  7. Copy the RustFS volume and pin the old `S3_*` values in `.env`.
  8. Set `.env` `DATABASE_URL` to `heftra`.
  9. `docker compose up -d`.
  10. Restart the dev servers.
- [x] 6.2 Add the external checklist to the runbook:
  - Cloudflare tunnel hostnames (`heftra.com`, `app.`, `api.`) and the 301 rule for `heftra.ai`, `www.heftra.ai` and `www.heftra.com`;
  - mailboxes `hello@` and `privacy@`;
  - Clerk application name and allowed origins;
  - the Dokploy repository URL and env;
  - production `WEB_API_CORS_ORIGINS`.

## 7. Verify and land

- [x] 7.1 `uv run pytest -q`, the web vitest suite, `tsc --noEmit`, and the landing checks (3.7) all pass at the baselines plus the new tests. `openspec validate rename-to-heftra --strict` passes.
- [x] 7.2 `git grep -niE "steelyard"` outside `openspec/changes/archive`, `docs/superpowers` and lockfiles. Matches may remain only in:
  - `scripts/rename-dev-db.sh` usage;
  - the CLAUDE.md migration note;
  - this change's artifacts and runbook.
- [x] 7.3 Commit on `main` in two commits: (1) brand, names and domain (web, landing, backend titles, docs, specs, this change); (2) dev infrastructure (compose, defaults, script), with the runbook path in its message. `site.ts` and the READMEs mix name and domain edits in the same lines, so a separate domain commit was folded into the first.

## 8. Repository rename (confirm first)

- [x] 8.1 Check that `HadiSDev/heftra` does not already exist (`gh repo view HadiSDev/heftra`). Then ask the owner for explicit confirmation, and only then run `gh repo rename heftra -R HadiSDev/steelyard`.
- [x] 8.2 `git remote set-url origin git@github.com:HadiSDev/heftra.git`, `git fetch`, and push `main` once the owner says to push.
- [x] 8.3 Update the Claude memory entries that name Steelyard (`infra-port-conflicts.md`: the API title "Heftra Web API" and the compose names). Hand the owner the runbook for the folder move.

## 9. Product screenshots

- [ ] 9.1 Once the owner has the renamed web app running on 3100 with the Nordlys Byg demo company:
  - recapture the five dark screenshots with `scripts/capture-screenshots.ts` (Clerk impersonation, dev instance only);
  - inspect each capture for the Heftra lockup and for no real names;
  - revoke the impersonation session;
  - commit the new captures.
