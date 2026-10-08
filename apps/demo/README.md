# Hosted demo (demo.heftra.com)

A temporary copy of the web app for showing Heftra to investors. It serves only
the fictional **Nordlys Byg A/S**, never customer or dev data, behind one shared
demo login. Visitors see every option an organization admin has, but nothing
they do is saved.

| Service       | What it is                                                                 |
| ------------- | -------------------------------------------------------------------------- |
| `postgres`    | PostgreSQL 16, initialised from `postgres/demo.sql.gz` on first start      |
| `link-org`    | One-shot step: points the demo organization at the Clerk org on each start |
| `reset`       | Restores the original data every night at 03:00 (Europe/Copenhagen)        |
| `web-api`     | `apps/web-api/Dockerfile`; applies migrations, then serves on 8100         |
| `demo-erp`    | `erp/`; a stand-in ERP that serves each invoice's PDF on 8001              |
| `web`         | `apps/web/Dockerfile`; the TanStack Start server on 3100                   |
| `cloudflared` | Cloudflare Tunnel; nothing is published on the host                        |

The demo has no file store, AI services or worker. Pages read precomputed data,
so they need none.

## What visitors can do

The demo user has the **demo** role. It sees everything an organization admin
sees, but changes nothing:

- **Every admin control is shown**: line and invoice editing, spend trees,
  agreement upload and review, finding alternatives, companies and their ERP
  connection, organization settings and members. System-admin tools stay
  hidden.
- **Every save is refused.** The web API answers any change from the demo role
  with "This is a demo, so changes aren't saved." The web app shows that as a
  toast and keeps the dialog open.
- **Changes Clerk would make directly are intercepted too**: profile, email,
  password, sessions, members and the organization logo.
- **A banner on every page** tells visitors they're in the demo.

Opening an agreement's original PDF shows a note instead, because the demo has
no file store.

## Nightly reset

Visitors can't change the data, but as a safety net the `reset` service
restores the original data every day at 03:00 Europe/Copenhagen
(`DEMO_RESET_AT` changes the time). It:

1. loads `postgres/demo.sql.gz` into a separate database;
2. links it to the Clerk org;
3. keeps `demo-erp`'s registered credentials;
4. swaps it in for the live database in under a second.

To reset by hand:

```bash
docker compose run --rm reset reset-now
```

If the dump's schema revision differs from the live database's (the code gained
a migration and the dump wasn't rebuilt), the reset refuses and logs it, and the
live data stays as it is. Rebuild the dump and redeploy to fix that.

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
   Nordlys Byg with the role **Member**. Set its public metadata to
   `{"demo": true}`, and under **Sessions → Customize session token** add the
   claim `"demo": "{{user.public_metadata.demo}}"` next to `system_admin`. The
   web API gives a user with that claim the **demo** role, which sees what an
   organization admin sees and saves nothing. Removing `demo` from the user's
   public metadata makes it a plain member again.
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
| `DEMO_RESET_AT`         | time of the nightly reset (default `03:00`)   |

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
