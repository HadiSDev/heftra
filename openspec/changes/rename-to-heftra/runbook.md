# Heftra rename: owner runbook

These steps follow the code change on `main` and the GitHub rename
(`HadiSDev/steelyard` → `HadiSDev/heftra`). They change things only you should
change: your running stack, your `.env` files, your folders, and outside
services. Run them in order.

## 1. Stop everything that has the folder open

- Close every Claude Code / Kilo session on this repository, including those in
  `.claude/worktrees/*` and `.kilo/worktrees/*`.
- Stop the dev servers: web (3100), web API (8100), landing (3200), and the
  pipeline worker.

## 2. Take the old stack down

The compose file is now `name: heftra`, so name the old project explicitly:

```bash
cd ~/repos/spend-predictor-rag
docker compose -p steelyard down
```

`pgdata/` and `qdrant_storage/` are bind mounts and move with the folder. The
RustFS data lives in the Docker volume `steelyard_rustfs_data`, which step 6
carries across.

## 3. Move the folder and repair the worktrees

```bash
mv ~/repos/spend-predictor-rag ~/repos/heftra
cd ~/repos/heftra
git worktree repair .claude/worktrees/* .kilo/worktrees/*
git worktree list            # every path now starts with ~/repos/heftra
git remote -v                # git@github.com:HadiSDev/heftra.git
```

## 4. Carry Claude Code's project memory across

Claude Code keys project memory by the folder path. Copy it rather than move it,
so the old copy stays as a fallback:

```bash
cp -a ~/.claude/projects/-home-hadi-repos-spend-predictor-rag \
      ~/.claude/projects/-home-hadi-repos-heftra
```

## 5. Rebuild the Python environments

The `.venv` entry points and editable installs hold absolute paths to the old
folder:

```bash
cd ~/repos/heftra
rm -rf .venv && uv sync
```

Do the same in any worktree that has its own `.venv`. `node_modules` folders use
relative links and normally keep working. Only if a `./node_modules/.bin/…`
command fails, re-run `bun install` in that app.

## 6. Rename the dev data

```bash
cd ~/repos/heftra
docker compose up -d postgres
scripts/rename-dev-db.sh                 # steelyard -> heftra; --from spend_predictor for older stacks

docker volume create heftra_rustfs_data
docker run --rm -v steelyard_rustfs_data:/from:ro -v heftra_rustfs_data:/to \
  alpine cp -a /from/. /to/
```

Then edit `~/repos/heftra/.env`. The database moves to the new name. The
object store keeps its old bucket and keys, because they live inside the copied
volume:

```dotenv
DATABASE_URL=postgresql://heftra:heftra@localhost:5432/heftra
S3_BUCKET=steelyard
S3_ACCESS_KEY=steelyard
S3_SECRET_KEY=steelyard-dev-secret
```

Apply the same `DATABASE_URL` change to any worktree `.env` that sets it.

## 7. Bring it back up

```bash
docker compose up -d
cd apps/web-api && uv run alembic current    # same head as before
```

Restart the dev servers. For the landing site, clear its caches first:

```bash
cd apps/landing && rm -rf node_modules/.vite .astro && ./node_modules/.bin/astro dev --port 3200
```

When everything works, you can drop the old volume and memory copy:
`docker volume rm steelyard_rustfs_data` and
`rm -rf ~/.claude/projects/-home-hadi-repos-spend-predictor-rag`.

## 8. Outside services

- **Cloudflare** (zone `heftra.com`):
  - tunnel public hostnames `heftra.com` → `http://landing:8080`, plus
    `app.heftra.com` and `api.heftra.com` for the app and API when they deploy;
  - proxied DNS records for `www.heftra.com`;
  - in the `heftra.ai` zone, proxied records for `heftra.ai` and
    `www.heftra.ai`;
  - a redirect rule sending `www.heftra.com`, `heftra.ai` and `www.heftra.ai`
    to `https://heftra.com` with a 301, keeping the path and query string.
- **Email**: mailboxes or aliases for `hello@heftra.com` and
  `privacy@heftra.com`.
- **Clerk**: rename the application to Heftra and add `https://app.heftra.com`
  to the allowed origins of the production instance.
- **Dokploy**:
  - point the landing service at `HadiSDev/heftra` (GitHub redirects the old
    URL, but don't rely on it);
  - keep compose path `apps/landing/docker-compose.yml`;
  - check that `TUNNEL_TOKEN` is set.
- **Production web API**: set `WEB_API_CORS_ORIGINS` to
  `https://app.heftra.com,https://heftra.com`, and set `DEMO_BOOKING_URL`.

## Rollback

```bash
scripts/rename-dev-db.sh --from heftra --to steelyard
gh repo rename steelyard -R HadiSDev/heftra
mv ~/repos/heftra ~/repos/spend-predictor-rag && cd ~/repos/spend-predictor-rag \
  && git worktree repair .claude/worktrees/* .kilo/worktrees/*
```

Then revert the rename commits.
