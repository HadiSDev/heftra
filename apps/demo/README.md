# Hosted demo (demo.heftra.com)

A temporary, read-only copy of the web app for showing Heftra to investors. It
serves only the fictional **Nordlys Byg A/S**, never customer or dev data, behind
one shared demo login.

| Service       | What it is                                                                 |
| ------------- | -------------------------------------------------------------------------- |
| `postgres`    | PostgreSQL 16, initialised from `postgres/demo.sql.gz` on first start      |
| `link-org`    | One-shot step: points the demo organization at the Clerk org on each start |
| `web-api`     | `apps/web-api/Dockerfile`; applies migrations, then serves on 8100         |
| `demo-erp`    | `erp/`; a stand-in ERP that serves each invoice's PDF on 8001              |
| `web`         | `apps/web/Dockerfile`; the TanStack Start server on 3100                   |
| `cloudflared` | Cloudflare Tunnel; nothing is published on the host                        |

The demo has no file store, AI services or worker. Pages read precomputed data,
so they need none. The only thing that doesn't work is opening an agreement's
original PDF.

## Invoice documents

The app fetches an invoice's document live from the company's ERP. The demo
company's integration is the mock ERP type, so `demo-erp` plays that ERP:

- `GET /api/v1/documents/{voucher}` renders the invoice posted under that
  voucher as a PDF, from the demo database: supplier, buyer, lines and totals.
  PDFs are rendered on first request and cached.
- On start, it stores its own address (`http://demo-erp:8001`) as the
  integration's credentials, encrypted with `DEMO_CREDENTIAL_KEY`, which the web
  API uses to decrypt them.
- `scripts/attach_invoice_documents.py` runs during the dump build. It gives
  every demo invoice a processed document record with its totals, as a real ERP
  sync would.

## The demo data

`scripts/build-demo-db.sh` builds `postgres/demo.sql.gz` from scratch:

1. It starts a throwaway PostgreSQL and applies the migrations.
2. It copies the emission factor sets and price indices (public reference data)
   from the dev database.
3. It creates the demo organization and runs the demo-company seed.

Rebuild it after schema or seed changes, then redeploy with the `demo_pgdata`
volume removed: the dump only loads into an empty data directory.

## Clerk (production instance)

The web app talks to Clerk's production instance for `heftra.com`. Set it up once:

1. In the Clerk dashboard, create the production instance on `heftra.com`, and
   add the DNS records it lists in Cloudflare.
2. Under **User & authentication**, enable email address + password.
3. Under **Organizations**, enable organizations.
4. Create the organization **Nordlys Byg** and copy its id (`org_…`).
5. Create the user `demo@heftra.com` with a strong password, and add it to
   Nordlys Byg with the role **Member**. Members can read everything but change
   nothing, because every write needs admin or moderator.
6. Copy the production keys: the publishable key `pk_live_…`, the secret key
   `sk_live_…`, and the Frontend API URL (`https://clerk.heftra.com`).

## Dokploy

Create a Compose service from this repository with compose path
`apps/demo/docker-compose.yml`, and set:

| Variable                | Value                                         |
| ----------------------- | --------------------------------------------- |
| `DEMO_DB_PASSWORD`      | a long random string                          |
| `DEMO_CLERK_ORG_ID`     | the Nordlys Byg org id (`org_…`)              |
| `CLERK_ISSUER`          | `https://clerk.heftra.com`                    |
| `CLERK_PUBLISHABLE_KEY` | `pk_live_…`                                   |
| `CLERK_SECRET_KEY`      | `sk_live_…`                                   |
| `TUNNEL_TOKEN`          | the tunnel's token                            |
| `DEMO_LOGIN_PASSWORD`   | the demo user's password, shown on sign-in    |
| `DEMO_LOGIN_EMAIL`      | `demo@heftra.com` (default)                   |
| `DEMO_CREDENTIAL_KEY`   | a Fernet key (any; `demo-erp` re-registers)   |
| `DEMO_APP_URL`          | `https://demo.heftra.com` (default)           |
| `DEMO_API_URL`          | `https://demo-api.heftra.com` (default)       |

The publishable key, `DEMO_API_URL` and the demo login are baked into the web
build, so change them by redeploying. The sign-in page shows the demo login in a
"Demo access" box with a one-click sign-in, and pre-fills the password form. Any
build without `VITE_DEMO_EMAIL` and `VITE_DEMO_PASSWORD`, such as the real app,
shows no box.

In the tunnel, add these public hostnames:

- `demo.heftra.com` → `http://web:3100`
- `demo-api.heftra.com` → `http://web-api:8100`

## Sharing and ending it

Send the investor `https://demo.heftra.com`; the login is on the sign-in page,
so anyone with the link can get in. To revoke access, ban the demo user in
Clerk. Changing the password also works, but redeploy with the new
`DEMO_LOGIN_PASSWORD` so the page shows it.

Because the password is public, set these in Clerk:

- Under **User & authentication → Restrictions**, turn off "Allow users to
  delete their accounts", so a visitor can't remove the shared user.
- Keep an eye on the demo user: a visitor could change its password from the
  account portal. If that happens, reset it in Clerk. Bring the
stack down when the demo period is over.
