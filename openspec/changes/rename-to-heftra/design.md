## Context

The product was renamed once already (Spend Predictor → Steelyard, archived
change `2026-09-27-steelyard-rebrand`). That change set the patterns this one
reuses:

- `brand/` is the source of truth, and served copies are byte-tested against it.
- The `Logo` component and `Lockup.astro` inline outlined path data.
- A source scan in `apps/web/src/brand-scan.test.ts` and a build test in
  `apps/landing/tests/build/metadata.test.ts` keep legacy names out.
- `scripts/rename-dev-db.sh` renames a dev database in place.

What changed in the pack, compared with `HEAD`:

- **Changed**: the lockup SVGs and PNGs (new wordmark, viewBox
  `0 -12.8 448.3 98.0`) and `social/og-image-1200x630.png`.
- **Unchanged, byte-identical**: the symbol and app-icon SVGs and every file in
  `brand/favicon/`.

So no favicon is re-copied and no symbol geometry changes.

State of the repository at proposal time:

- About 275 "steelyard" occurrences in tracked files, most of them in
  `apps/landing` (33 files).
- The `landing-site` change is still open (60/61 tasks; the Lighthouse run is
  pending). Its delta specs name Steelyard and `steelyard.com`.
- Four worktrees live inside the repo folder (`.claude/worktrees/*`,
  `.kilo/worktrees/*`), and other agents may be working in them.
- `origin` is `git@github.com:HadiSDev/steelyard.git`.
- The root compose stack bind-mounts `pgdata/` and `qdrant_storage/`, but
  RustFS uses the **named volume** `rustfs_data`, which Docker prefixes with
  the compose project name (`steelyard_rustfs_data`).

## Goals / Non-Goals

**Goals:**

- Every name a person reads says Heftra.
- Every production URL and contact address is on `heftra.com`.
- Dev infrastructure is named `heftra`, with a path that keeps existing dev data.
- The GitHub repo is `HadiSDev/heftra`, and the owner has a safe runbook to
  move the local folder.
- Guards (source scans, build tests) fail if "Steelyard" creeps back in.

**Non-Goals:**

- Renaming packages, Python modules or the mark ("Counterweight").
- Changing the tagline, palette or any visual design beyond the wordmark.
- Rewriting history: archived changes, `docs/superpowers` and commit messages
  keep their names.
- Configuring Cloudflare, mailboxes or Clerk. Those are owner steps, listed in
  the runbook.
- Rewriting the legal pages around VectorLab ApS as controller. That is a
  separate, already-offered follow-up.

## Decisions

### 1. `heftra.com` is canonical; `heftra.ai` redirects

The owner chose `heftra.com` as the main domain. A `.com` is what people type
and trust by default for a B2B product, and it is the domain `brand/README.md`
already uses for the OG image. `heftra.ai` is kept to catch AI-flavoured links
and to protect the name. It redirects to
`https://heftra.com` with 301s that preserve the path; so do `www.heftra.ai` and
`www.heftra.com`. The redirects are done by a Cloudflare redirect rule, not by
the landing container. The container only ever serves one host, so nginx needs
no change.

Subdomains follow the existing pattern: `app.heftra.com` and `api.heftra.com`.
Contact addresses are `hello@` and `privacy@heftra.com`.

*Alternative*: `.ai` canonical with `.com` redirecting. Rejected because the
owner chose `.com`.

### 2. One rename sweep, guarded by scans, not hand-picked edits

Edits go file by file, reading context rather than running a blind `sed`. This
matters because:

- "Steelyard" sometimes sits in grammatical context that needs rewording (a
  steelyard is also a weighing device, and the landing copy may play on it).
- Lowercase `steelyard` appears in identifiers and defaults.

Then the existing guards are extended so the rename stays done:

- `brand-scan.test.ts` (web) adds `steelyard` to its forbidden names.
- The landing metadata build test adds `steelyard` to its legacy-name check.
- A landing build test asserts that the built site contains no `steelyard`
  (case-insensitive) and that every product-domain email ends in `@heftra.com`.

The final check is `git grep -i steelyard` outside
`openspec/changes/archive`, `docs/superpowers` and lockfiles. Allowed leftovers:

- `scripts/rename-dev-db.sh`, where the old name is a valid `--from` value;
- the CLAUDE.md migration note;
- the runbook in this change;
- this change's own artifacts.

### 3. Wordmark geometry is re-copied, the symbol is not

`apps/web/src/components/brand/logo.tsx` and
`apps/landing/src/components/brand/Lockup.astro` take the new wordmark path and
viewBox from `heftra-lockup-black.svg`. Their existing path-parity tests are
repointed at `brand/svg/heftra-*.svg`.

The aspect ratio changes ("Heftra" is shorter than "Steelyard"). Where a
component sets an explicit width or height from the old ratio, it is recomputed
from the new viewBox. The 80 px minimum lockup width still holds.

### 4. Product screenshots are recaptured

The five landing screenshots (`apps/landing/src/assets/product/*-dark.png`) show
the web app's sidebar, which carries the lockup. They are recaptured after the
web app is renamed, with the existing
`apps/landing/scripts/capture-screenshots.ts`:

- Clerk impersonation on the dev instance;
- the "Nordlys Byg A/S" demo company;
- the persona scrub.

This needs the owner's running web app (agents don't launch dev servers), and
the impersonation session is revoked afterwards.

### 5. Dev infrastructure renames to `heftra`, with a carry-across path

Defaults that become `heftra`:

- root `docker-compose.yml`: `name: heftra`;
- `POSTGRES_*`;
- the RustFS access key default (secret `heftra-dev-secret`);
- `web_api/config.py`: `DATABASE_URL` and `S3_BUCKET`;
- `db/session.py`;
- `.env.example`.

The landing deploy compose becomes `name: heftra-landing`.

`scripts/rename-dev-db.sh` defaults to `--from steelyard --to heftra`. It
already handles the general case and is idempotent, so only its defaults and
usage text change. A developer still on `spend_predictor` runs it with
`--from spend_predictor`.

The RustFS volume cannot be renamed in Docker. The runbook copies it once, with
the old project stopped:

```bash
docker volume create heftra_rustfs_data
docker run --rm \
  -v steelyard_rustfs_data:/from:ro \
  -v heftra_rustfs_data:/to \
  alpine cp -a /from/. /to/
```

Inside the copied volume, objects still live in the bucket `steelyard`, under
the old root credentials. RustFS is not documented to tolerate a root-credential
change on an existing data directory, and copying objects between buckets is
more machinery than dev data deserves. So the runbook's carry-across step pins
the three old values in the developer's `.env`:

- `S3_BUCKET=steelyard`
- `S3_ACCESS_KEY=steelyard`
- `S3_SECRET_KEY=steelyard-dev-secret`

A fresh stack gets `heftra` everywhere.

*Alternatives*:

- Pinning the volume's name to `steelyard_rustfs_data` in compose. Rejected
  because it bakes the old name into the file this change is cleaning.
- A bucket-copy script. Rejected as unnecessary for disposable dev data that has
  a zero-code override.

Agents verify the script and the volume copy against throwaway containers and
volumes. They never run them against the owner's live stack, and never edit any
`.env` (root, app or worktree).

### 6. The landing theme key resets rather than migrates

`steelyard-theme` becomes `heftra-theme` without reading the old key. The site
has not launched, so no real visitor has a stored preference. A migration shim
would be dead code from day one.

### 7. Order: code first, then GitHub, then the folder

1. **Code change on `main`** in the current folder. It is committed as three
   commits: brand and names, domain, infra.
2. **GitHub rename**: `gh repo rename heftra -R HadiSDev/steelyard`, then
   `git remote set-url origin git@github.com:HadiSDev/heftra.git`. This is an
   outward-facing action, so the agent asks for explicit confirmation
   immediately before running it, and first checks that `HadiSDev/heftra` does
   not already exist. GitHub redirects the old URL, so other clones and
   worktrees keep working until their remotes are updated.
3. **Local folder move**, done by the owner from the runbook
   (`openspec/changes/rename-to-heftra/runbook.md`) once no agent sessions or
   dev servers are running:

   ```bash
   docker compose -p steelyard down      # the project name changes anyway
   mv ~/repos/spend-predictor-rag ~/repos/heftra
   cd ~/repos/heftra && git worktree repair
   cp -a ~/.claude/projects/-home-hadi-repos-spend-predictor-rag \
         ~/.claude/projects/-home-hadi-repos-heftra
   ```

   Then the owner rebuilds the Python virtualenvs (`.venv` entry-point
   shebangs hold absolute paths), runs the database rename, copies the volume,
   updates `.env`, and brings the stack up.

The folder move comes last, and is the owner's, because it changes the working
directory of every running session, including the one doing this change. The
Claude Code project memory is keyed by the absolute path, so it is copied
rather than moved, which leaves the old one as a fallback. Worktrees under
`.claude/worktrees` and `.kilo/worktrees` move with the folder, and
`git worktree repair` rewrites their links in both directions.

### 8. The open `landing-site` change is edited in place

`landing-site` has not been archived, so the `landing-site` and `demo-requests`
specs exist only as its deltas. Its proposal, design, tasks and delta specs are
updated to say Heftra and `heftra.com`, so that archiving it produces correct
living specs.

The alternative was to archive `landing-site` first and then modify its specs
here. Rejected because that would archive a change with an open task (10.4,
Lighthouse) just to satisfy ordering.

## Risks / Trade-offs

- **[Agents in other worktrees keep writing "Steelyard" on their branches]** →
  The scans fail on their branches after they rebase onto `main`, which points
  them at the leftovers. The commit message names the new guards.
- **[The folder move breaks a running session or dev server]** → The runbook
  starts with "stop all sessions and servers", and the move is the owner's step,
  never an agent's.
- **[RustFS rejects changed root credentials on a carried volume]** → Avoided
  by pinning the old S3 values in `.env` for carried stacks. Fresh stacks never
  see the old values.
- **[Hadi's landing dev server serves stale content after the build tests]** →
  Build verification runs in an isolated copy in the scratchpad (created with
  `mkdir -p`, then rsync with symlinked `node_modules`). If a build ever runs in
  `apps/landing`, the owner is told to restart dev with `.astro` and
  `node_modules/.vite` cleared.
- **[Screenshots can't be recaptured in this session]** (the web app isn't
  running) → The landing still builds with the old captures. The recapture
  stays an open task, and its only visible effect is the sidebar wordmark
  inside the frames.
- **[Old links: steelyard.com was never ours]** → No redirect or SEO
  carry-over is needed; nothing was ever published there.
- **[`gh repo rename` collides or loses webhooks/deploy keys]** → The agent
  checks that the target name is free first. GitHub keeps webhooks, keys and
  redirects across a rename. Dokploy's repository URL is updated by the owner
  (runbook step).

## Migration Plan

1. Land the code change on `main`, in three commits: brand and names, domain,
   infra.
2. Confirm with the owner, rename the GitHub repo, and update `origin`. Push.
3. Owner, following the runbook:
   - stop dev servers and agent sessions;
   - `docker compose -p steelyard down`;
   - move the folder and run `git worktree repair`;
   - copy the Claude memory dir;
   - rebuild the virtualenvs;
   - `docker compose up -d postgres`, then `scripts/rename-dev-db.sh`;
   - copy the RustFS volume and pin the old S3 values in `.env`;
   - update `DATABASE_URL` in `.env`;
   - `docker compose up -d`, and restart the dev servers.
4. Owner, externally:
   - Cloudflare: tunnel hostnames `heftra.com`, `app.`, `api.`, and the
     redirect rule for `heftra.ai`, `www.heftra.ai` and `www.heftra.com`;
   - mailboxes `hello@` and `privacy@heftra.com`;
   - Clerk application name and allowed origins;
   - the Dokploy repository URL;
   - `WEB_API_CORS_ORIGINS` and `DEMO_BOOKING_URL` in production.
5. Recapture the product screenshots against the renamed web app.

**Rollback**: revert the commits. `rename-dev-db.sh --from heftra --to steelyard`
restores the database. `gh repo rename steelyard` restores the repo. Moving the
folder back and running `git worktree repair` restores the local layout.

## Open Questions

None blocking. The owner may later prefer a different `S3_BUCKET` carry-over
(a real bucket copy), and that would be an isolated follow-up.
