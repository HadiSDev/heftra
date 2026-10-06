# Heftra landing site

The public marketing site for Heftra, served at `https://heftra.com`. It is
a static [Astro](https://astro.build) site: Tailwind CSS v4, Geist, GSAP for
scroll motion, and no server runtime.

## Run it

```bash
cp .env.example .env
bun install
./node_modules/.bin/astro dev --port 3200
```

| Variable          | Local                   | Production                  |
| ----------------- | ----------------------- | --------------------------- |
| `PUBLIC_SITE_URL` | `http://localhost:3200` | `https://heftra.com`        |
| `PUBLIC_APP_URL`  | `http://localhost:3100` | `https://app.heftra.com`    |
| `PUBLIC_API_URL`  | `http://localhost:8100` | the web API's public origin |

The build fails when any of them is missing.

## Demo requests

Every "Get a demo" button leads to `/demo`. The form posts to the web API's
`POST /api/v1/public/demo-requests`, which stores the request and returns the
booking link from its own `DEMO_BOOKING_URL`. The booking link is never part of
this site. For local testing, the web API needs `http://localhost:3200` in
`WEB_API_CORS_ORIGINS`.

## Content

Copy that changes on its own lives in `src/content/` and is validated by the
schemas in `src/content.config.ts`:

| File                | What it holds                                                      |
| ------------------- | ------------------------------------------------------------------ |
| `features.yaml`     | One block per product capability, with its screenshot              |
| `integrations.yaml` | ERP systems; mark one `live` only when its connector ships         |
| `pricing.yaml`      | Plans; `null` prices render as "Custom"                            |
| `faq.yaml`          | Questions and answers, also emitted as `FAQPage` structured data   |
| `outcomes.yaml`     | Approved result figures; the section is hidden while it is empty   |
| `testimonials.yaml` | Real customer quotes only; the section is hidden while it is empty |

An outcome with `draft: true` shows a "Draft" marker in development and fails a
production build, so unapproved figures cannot ship.

## ERP logos

The integrations strip shows each vendor's official logo, unmodified, from
`src/assets/integrations/`. Logos that ship in a single colour are drawn in the
vendor's own brand colour (`logoColor` in `integrations.yaml`); full-colour logos
are used as published. Every logo sits on a white plate in both themes. Logos
are imported through `astro:assets` and rendered with `<Image format="svg">`, so
they stay vector and get hashed, cacheable URLs; single-colour logos use that same
asset URL as a CSS mask.

| File               | Source                                                                         |
| ------------------ | ------------------------------------------------------------------------------ |
| `dynamics-365.svg` | Wikimedia Commons, "Microsoft Dynamics 365 Logo (2021–present)", public domain |
| `sap.svg`          | Wikimedia Commons, "SAP 2011 logo", public domain                              |
| `netsuite.svg`     | netsuite.com site header (`Oracle-NetSuite-Logo.svg`), full colour             |
| `ifs.svg`          | ifs.com content hub (`ifs_logo_negative_rgb`), drawn in IFS purple `#360065`   |
| `visma.svg`        | visma.com site header, black                                                   |
| `billy.svg`        | billy.dk site header (Billy by Shine), brand teal `#002E33`                    |

The logos are the vendors' trademarks, shown only to say which systems
Heftra connects to.

## Product screenshots

Screenshots are real captures of the web app, rendered with `astro:assets`
`<Picture>` as AVIF and WebP at several widths, and stored in `src/assets/product/`
as `<name>-dark.png` (the product frame is always dark). Until a capture exists, its frame
shows a "Screenshot pending" panel and the build tests fail. To capture them,
run the web app with demo data and sign in through Clerk impersonation (dev
instance only):

```bash
CAPTURE_SIGN_IN_URL="$(clerk impersonate <user> --print)" \
CAPTURE_COMPANY_ID=<demo company id> \
CAPTURE_AGREEMENT_PATH=/agreements/<agreement id> \
  node --experimental-strip-types scripts/capture-screenshots.ts
```

The demo company is the fictional "Nordlys Byg A/S", seeded with
`uv run python apps/ai-api/scripts/demo_company` from the repository root. Before
each shot the script hides development overlays (Clerk's impersonation badge,
TanStack devtools) and replaces the signed-in person and organization with a
persona ("Mette Hansen", "Nordlys Byg"), so no real names reach the site.

## Tests

```bash
./node_modules/.bin/astro check
./node_modules/.bin/vitest run                         # unit tests; build tests need a fresh `astro build`
./node_modules/.bin/astro build && ./node_modules/.bin/playwright test
```

The Playwright run starts its own preview on port 4322.

## Deploy (Dokploy + Cloudflare Tunnel)

The site ships as one container: a multi-stage `Dockerfile` builds it with Astro
and serves `dist/` from unprivileged nginx on port 8080 (`deploy/nginx.conf`:
`/demo` → `/demo/` redirects, the branded 404, a year of caching for `/_astro/`,
security headers, `/healthz`). `docker-compose.yml` runs it next to `cloudflared`,
so nothing is published on the host.

1. **Cloudflare**: in Zero Trust → Networks → Tunnels, create a tunnel and copy
   its token. Add the public hostname `heftra.com` → `http://landing:8080`.
   `heftra.com` is the only host the site serves: add a redirect rule that sends
   `www.heftra.com`, `heftra.ai` and `www.heftra.ai` to `https://heftra.com`
   with a 301, keeping the path and query string. Those hostnames need proxied
   DNS records so the rule can run.
2. **Dokploy**: create a Compose service from this repository with compose path
   `apps/landing/docker-compose.yml`, and set these environment variables:

   | Variable          | Value                              |
   | ----------------- | ---------------------------------- |
   | `TUNNEL_TOKEN`    | the tunnel token (required)        |
   | `PUBLIC_SITE_URL` | `https://heftra.com` (default)     |
   | `PUBLIC_APP_URL`  | `https://app.heftra.com` (default) |
   | `PUBLIC_API_URL`  | `https://api.heftra.com` (default) |

   The `PUBLIC_*` values are baked in at build time, so change them by
   redeploying. Don't add a Dokploy domain for this service; the tunnel routes
   traffic.

3. **Demo form**: the web API at `PUBLIC_API_URL` must be reachable and list
   `https://heftra.com` in `WEB_API_CORS_ORIGINS`, with `DEMO_BOOKING_URL` set.

To try the image locally:

```bash
docker build -t heftra-landing .
docker run --rm -p 8088:8080 heftra-landing
```
