## Why

Heftra has a working product (ERP sync, AI categorization, cheaper alternatives,
agreement compliance, spend-based emissions) but no public face: there is nowhere
to send a prospect, nothing to link from LinkedIn or an email, and no page that
explains the product before someone signs in. A marketing site that tells the
"know the true price of everything you buy" story is the first thing a buyer or
investor sees, so it has to look as premium as the product is serious.

## What Changes

- Add a new app, `apps/landing`, an Astro static site (bun, Tailwind v4, Geist)
  that serves the public marketing page for Heftra.
- The home page carries every section a SaaS AI product landing page is expected
  to have: sticky navigation, a hero with the value proposition and primary/secondary
  CTAs, an integrations strip, the problem, how it works (connect → categorize →
  save), a feature showcase per product capability, product imagery, outcome
  metrics, an AI-trust and data-security section (EU hosting, tenant isolation,
  human review of AI output), pricing, an FAQ, a final call to action, and a footer.
- Testimonials are a content-driven section that renders only when real quotes
  exist; the site ships no invented customers, logos, quotes or statistics.
- Cinematic scroll storytelling (depth layers, text reveals, a pinned
  "how it works" sequence) in the monochrome Heftra brand, with a complete
  reduced-motion fallback and no layout shift.
- Supporting pages: privacy policy, terms, and a branded 404.
- Search and sharing metadata: per-page title and description, canonical URL,
  Open Graph and Twitter cards from the brand pack, `sitemap.xml`, `robots.txt`,
  and `Organization`/`SoftwareApplication` structured data.
- Demos are free but gated: every "Get a demo" CTA leads to a `/demo` request form
  (name, work email, company, size, consent). The web API stores the request and
  only then returns the booking link, so the link never appears on the site.
- A new public, unauthenticated web-api endpoint receives demo requests, with
  honeypot, minimum fill time and per-IP rate limiting, and a `demo_requests` table.
- "Sign in" links point at the web app; there is no self-serve sign-up yet, so no
  free-trial or sign-up link is offered.
- **BREAKING (repository layout)**: `apps/` will contain five apps instead of
  exactly four; the `monorepo-layout` requirement is updated to include
  `apps/landing`.

## Capabilities

### New Capabilities

- `landing-site`: The public Heftra marketing site in `apps/landing` — the app
  itself (stack, build, dev port, configuration), the home page sections and their
  content rules, supporting pages, motion and accessibility, and SEO/sharing metadata.

- `demo-requests`: The web API's public endpoint that accepts, validates, rate-limits
  and stores demo requests and returns the booking link.

### Modified Capabilities

- `monorepo-layout`: "Every runnable app lives under apps/" now lists `apps/landing`
  as a fifth app.
- `brand-identity`: the brand source, product name, logo and metadata requirements
  now apply to the landing site as well as the web app (served assets are byte-copies
  of `brand/`, the logo is drawn from its outlines in ink, the head carries the
  favicon set, theme color and OG card).

## Impact

- **New code**: `apps/landing/` (Astro project, components, content, public assets
  copied from `brand/`, its own `bun.lock`).
- **Dependencies**: `astro`, `@astrojs/sitemap`, `@tailwindcss/vite`, `tailwindcss`,
  `@fontsource-variable/geist`, `@fontsource-variable/geist-mono`, `gsap`. No changes
  to the Python workspace or to `apps/web`'s dependencies.
- **Dev infrastructure**: a new dev port (3200) beside web (3100) and web API (8100).
- **Product screenshots**: the site needs real captures of the web app (dashboard,
  spend lines, alternatives, agreements); these are taken from the running app with
  seeded demo data, not mocked up.
- **API**: one new unauthenticated route, `POST /api/v1/public/demo-requests`, a
  `DemoRequest` model and migration `0025_demo_requests`, and the settings
  `DEMO_BOOKING_URL` and `DEMO_REQUEST_RATE_LIMIT`; the landing origin is added to
  `WEB_API_CORS_ORIGINS`.
