## Context

Steelyard is a B2B spend-analytics product for EU mid-market companies and the
bookkeeping firms that serve them. The product lives in `apps/web` (TanStack Start,
React, Tailwind v4, Geist, bun) behind Clerk sign-in. There is no public page.

The brand pack in `brand/` is strict: ink `#0A0A0A` and white only, the
Counterweight mark, and a wordmark that is never retyped. The web app already
expresses this as monochrome tokens (`--canvas`, `--foreground`, `--muted`,
`--border`, …) with semantic colours (`--success`, `--warning`, `--destructive`)
used only for meaning. The landing site has to feel cinematic and premium while
staying inside that palette.

Repository rules that shape the code: no inline imports, no one-line `if`s,
braces always, few components per file, sub-folders once a folder grows. Frontend
projects use bun and their committed `bun.lock`; agents call
`./node_modules/.bin/<tool>` directly rather than package-manager scripts.

## Goals / Non-Goals

**Goals:**

- A static Astro site in `apps/landing` with every section a SaaS AI landing page
  needs (see the `landing-site` spec), deployable to any static host.
- Scroll storytelling with real depth, built so that every frame is also correct
  with motion off and with JavaScript off.
- The same visual language as the product: monochrome tokens, Geist, the
  Counterweight mark, real product screenshots.
- Content (features, pricing, FAQ, integrations, outcomes, testimonials) edited in
  typed content files, not in markup.

**Non-Goals:**

- A blog, changelog, docs site or careers page (the content-collection setup
  leaves room for them later).
- A CRM sync or notification email for demo requests: they are stored and can be
  read from the database; forwarding them is a follow-up.
- Localization (English only for now; Danish is a likely follow-up).
- Analytics and a cookie banner (no tracking ships, so no consent is needed yet).
- Billing and self-serve sign-up: the web app only has invite-based sign-in, so
  every primary CTA is "Get a demo" and pricing cards do not start checkout. When
  sign-up ships, `src/lib/links.ts` is the one place to change.

## Decisions

### Astro static output, standalone bun project

`apps/landing` is its own bun project with its own lockfile, like `apps/web`. No
root JS workspace is introduced. Astro gives zero-JS-by-default pages, a built-in
image pipeline, content collections with Zod schemas, and `@astrojs/sitemap`.

*Alternatives:* a marketing route inside `apps/web` (couples the public site to
Clerk and SSR, ships React to every visitor, and ties deploys together); Next.js
(heavier runtime for a page that is almost entirely static).

### Tailwind v4 with tokens mirrored from the web app

`src/styles/tokens.css` declares the same token names and values as
`apps/web/src/styles.css` (light on `:root`, dark on `.dark`) and maps them with
`@theme inline`. Mirroring rather than importing keeps the two apps independently
buildable; a unit test compares the token values in both files so they cannot
drift.

Landing-only additions are limited to: a larger display type scale, section
spacing, and depth tokens (`--depth-0-blur` … `--depth-5-scale`). The only
non-monochrome colour on the page is `--success`, used for saving amounts, exactly
as the product uses it.

*Alternative:* a shared `packages/tokens` — rejected for now; it would introduce
a JS workspace for one file.

### Logo as Astro components drawn from the pack's outlines

`src/components/brand/Lockup.astro` and `Symbol.astro` inline the path data from
`brand/svg/` with `fill="currentColor"`, `role="img"` and `aria-label="Steelyard"`,
and switch to the favicon geometry below 32 px. A test reads `brand/svg/*.svg` and
asserts the path data in the components is identical.

*Alternative:* `<img src="/logo.svg">` — cannot follow the theme via
`currentColor` without two files and a swap.

### Motion: GSAP + ScrollTrigger as one progressive-enhancement script

Following the epic-design depth system, every scene is built from layered elements
with a `data-depth` of 0–5. A single module, `src/scripts/motion/index.ts`, loaded
with a normal `<script>` tag (Astro bundles and defers it), runs only when
`prefers-reduced-motion` is `no-preference`. It is split by concern:

| Module | Technique (epic-design catalogue) | Where |
|---|---|---|
| `depth-parallax.ts` | 6-layer depth parallax, float loop on the hero visual | Hero, Final CTA |
| `text-reveals.ts` | Masked line reveal; word-by-word scroll lighting for the problem statement | Section headings, Problem |
| `pinned-steps.ts` | Pinned sticky scene with a scrub timeline; each step's screenshot crossfades and a clip-path wipe reveals the next | How it works |
| `stagger-grid.ts` | Stagger grid entrance, window-pane iris on the feature imagery | Features, Pricing, Outcomes |
| `counters.ts` | Number count-up when an outcome figure enters view | Outcomes |
| `rotating-words.ts` | Slot-machine word roll: "every EUR you spend" cycles through the codes DKK, SEK, NOK, PLN, GBP, CHF and USD, with the word's width easing to each currency; screen readers get a stable "EUR"; with reduced motion the word crossfades instead of rolling | Features heading |

The no-motion state is the default authored state: HTML and CSS render every
section complete. The script adds a `motion` class to `<html>` before applying
"from" states, so nothing is ever hidden unless the script that will reveal it is
running. On `(pointer: coarse)` the script halves parallax distances and skips
pinning. Only `transform`, `opacity`, `filter` and `clip-path` are animated;
`will-change` is set when a tween starts and cleared when it completes.

*Alternatives:* CSS scroll-driven animations (`animation-timeline: view()`) —
cleaner, but Safari/Firefox support is incomplete and pinning needs JS anyway;
Motion One — smaller but no pinning/scrub equivalent to ScrollTrigger.

### Hero composition

Depth-0: an ink canvas with a faint engineering grid (SVG pattern, blurred).
Depth-1: a soft white radial glow behind the product. Depth-2: two small companion
cards (a "categorized" line chip and a "−18% vs. agreement" saving chip in
`--success`) that hug the screenshot's edges and scatter outward on scroll-out.
Depth-3 (hero asset): a framed dashboard screenshot at ~60vw with a slow
6–10 s float loop and a perspective tilt that settles flat as you scroll.
Depth-4: headline, sub-line, CTAs. Depth-5: a few counterweight-circle particles.

The hero is always dark (ink canvas, white text) in both themes — it is the
page's visual anchor; the rest of the page follows the theme. The final CTA mirrors
the hero so the page is bookended in ink.

### Product imagery is captured, not drawn

Screenshots of the dashboard, spend lines, cheaper alternatives, agreement
compliance, suppliers and emissions views are captured from the running web app
with seeded demo data, using Playwright signed in through Clerk impersonation on
the dev instance, at 2× device scale in both themes. They are stored under
`src/assets/product/` and served through `astro:assets` (`<Picture>` with AVIF and
WebP). Screenshots are kept as complete images (backgrounds retained, per the
asset pipeline: UI captures are content, not cut-outs) and framed by a CSS
"window" component.

### Content collections

`src/content.config.ts` defines collections with Zod schemas:
`features`, `integrations` (`status: 'live' | 'coming-soon'`), `outcomes`
(each figure carries a `source` note), `pricing` (plans with monthly/annual
prices, feature list, `recommended`), `faq`, and `testimonials` (name, role,
company, quote, optional avatar; empty at launch). Sections read from these and
render nothing when a collection is empty. Only `outcomes` carries a `draft`
flag: a production build refuses draft outcomes, because performance figures must
be real. Pricing and legal copy are starter versions that ship as they are and
are edited in place later.

### Pricing

Steelyard is sold to mid-size and enterprise companies running enterprise ERPs.
Plans scale by legal entities, ERP connections and invoice-line volume. Prices are
in EUR, excluding VAT, with two months free on annual billing. No free trial is
advertised; every plan starts with a demo.

| Plan | Monthly | Annual (per month) | For | Includes |
|---|---|---|---|---|
| Business | €1,490 | €1,242 | Mid-size companies, one ERP | Up to 5 legal entities, 1 ERP connection, 50,000 lines/month, AI categorization, dashboard, supplier directory, cheaper alternatives |
| Group (recommended) | €3,900 | €3,250 | Groups across entities and ERPs | Everything in Business, up to 25 entities, multiple ERP connections, 250,000 lines/month, agreement compliance, spend-based emissions, one group spend tree |
| Enterprise | Custom | Custom | Complex ERP landscapes | Everything in Group, unlimited entities and volume, guided onboarding and account mapping, DPA and security review, uptime SLA, priority support, spend tree designed with the customer; CTA is "Talk to us" |

### Starter legal pages

`/privacy` and `/terms` are written as plain-language starter policies for an EU
B2B SaaS, each with a "Last updated" date:

- **Privacy**: Steelyard as controller for website and account data and as
  processor for customer ERP data; what is collected (account details, ERP spend
  data, uploaded agreements); purposes and lawful bases; EU hosting; sub-processor
  categories (hosting, authentication, AI inference); demo requests (name, work
  email, company, kept 24 months); retention and deletion when a company is
  removed; GDPR rights; no tracking cookies; contact
  `privacy@steelyard.com`.
- **Terms**: the service and accounts, subscription billing, customer
  data ownership, acceptable use, AI output as decision support that customers
  review, availability, liability cap, termination and data export, governing law
  (Denmark), contact `hello@steelyard.com`.

### Configuration

`astro.config.ts` reads `PUBLIC_SITE_URL`, `PUBLIC_APP_URL` and
`PUBLIC_API_URL` through Astro's `env` schema (`envField.string`, `context:
'client'`, `access: 'public'`), which fails the build when a required variable is
missing. A small `src/lib/links.ts` builds the sign-in, `/demo` and demo-request
endpoint URLs from them.

The production site origin is `https://steelyard.com` (apex, no `www`), matching
the OG image URL already given in `brand/README.md`. `.env.example` lists that as
the production value of `PUBLIC_SITE_URL`, with `http://localhost:3200` as the
local value; `www.steelyard.com` redirects to the apex at the host. The web app
is `https://app.steelyard.com` in production and `http://localhost:3100` locally,
which are the production and local values of `PUBLIC_APP_URL`.

### Folder layout

```
apps/landing/
  astro.config.ts  package.json  bun.lock  tsconfig.json  .env.example
  public/                      favicons, og image (copies of brand/)
  src/
    assets/product/            captured screenshots
    components/
      brand/                   Lockup, Symbol
      layout/                  Header, MobileMenu, Footer, ThemeToggle, SkipLink
      sections/                Hero, Integrations, Problem, HowItWorks,
                               Features, Outcomes, Security, Testimonials,
                               Pricing, Faq, FinalCta
      ui/                      Button, Badge, ProductFrame, SectionHeading,
                               PricingCard, FeatureBlock
    content/                   features/, pricing/, faq/, … (yaml/md)
    content.config.ts
    layouts/BaseLayout.astro   head, SEO, theme bootstrap, header/footer
    lib/                       links.ts, seo.ts (JSON-LD builders)
    pages/                     index.astro, privacy.astro, terms.astro, 404.astro
    scripts/motion/            one module per technique (above)
    scripts/theme.ts
    styles/                    tokens.css, global.css, motion.css
  tests/                       vitest unit tests + built-output checks
```

### Gated demo requests

Demos are free, but the booking link is only handed out after a visitor tells us
who they are. The landing site never contains the booking URL: it lives in
web-api's `DEMO_BOOKING_URL` and is returned in the response to an accepted
request.

**Endpoint.** `POST /api/v1/public/demo-requests` in a new
`web_api/routers/public_demo_requests.py`, keeping the `/api/v1` prefix every
router uses. It declares no auth dependency, only `get_session`. The body
(`schemas/demo_requests.py`) carries `name`, `email`, `company`, `company_size`
(`1-49`, `50-249`, `250-999`, `1000+`), optional `message` (at most 2,000
characters), `consent: true`, the honeypot `website`, and `rendered_at` (epoch
ms). The email is checked with a pattern validator rather than `EmailStr`, so no
new dependency is added. Responses: `201 {"booking_url": ...}` (null when
`DEMO_BOOKING_URL` is unset, and the page then says the team will email them),
`422` with field errors, `429` when rate-limited.

**Spam protection**, in `web_api/demo_requests/guard.py`:
- A filled honeypot or a submit sooner than 3 s after render is answered with the
  same `201` but nothing is stored and no booking link is returned to the bot.
- A per-client-IP sliding window (default 5 requests per hour, from
  `DEMO_REQUEST_RATE_LIMIT`) kept in process memory. web-api runs as one process
  today; a shared store is a follow-up if it scales out.

**Storage.** `db/models/demo_request.py`, a global (non-tenant) table
`demo_requests`: `id`, `name`, `email`, `company`, `company_size`, `message`,
`consented_at`, `source_ip`, `user_agent`, `created_at`. Migration
`0025_demo_requests`. Rows hold personal data, so the privacy policy names this
purpose and a 24-month retention.

**Landing.** `src/pages/demo.astro` with `components/demo/DemoForm.astro` and its
script `scripts/demo-form.ts`: client-side `required`/`type=email` for fast
feedback, server errors mapped onto fields, a live-region confirmation that shows
the "Choose a time" link. `WEB_API_CORS_ORIGINS` gains the landing origin
(`http://localhost:3200` locally, `https://steelyard.com` in production).

*Alternatives:* a hosted form (Tally, HubSpot): no backend work, but data leaves
our stack and the booking link is easy to reach without submitting. A Clerk
sign-up into a sandbox tenant: the most convincing demo, but a much larger change
to the web app.

### Interactive islands without a framework

The mobile menu, theme toggle, pricing period toggle and FAQ are small vanilla
TypeScript scripts scoped to their component (`<script>` in the `.astro` file).
The FAQ uses `<details>/<summary>` so it works with no JS at all. No React is
shipped to visitors.

### Testing

- Vitest: token parity with `apps/web`, logo path parity with `brand/svg`, brand
  asset byte-equality, content schema fixtures, JSON-LD builders.
- Built-output tests (Vitest over `dist/`): one `h1`, required anchors, absolute
  `og:image`, sitemap entries, no testimonials heading when the collection is empty,
  no legacy product names.
- Playwright smoke run against `astro preview`: mobile menu keyboard flow, theme
  persistence with no flash, reduced-motion emulation leaves all content visible.
- Lighthouse (mobile) run on the built site against the spec's budget.

## Risks / Trade-offs

- [GSAP pinning causes jank or layout shift on low-end devices] → pinning is off on
  coarse pointers; pinned scene heights are set in CSS, not measured in JS; CLS is
  part of the Lighthouse check.
- [Motion hides content if the script fails] → content is visible by default; the
  `motion` class that enables "from" states is added only by the running script.
- [Tokens drift from the web app] → parity test fails CI on any difference.
- [Screenshots go stale as the product changes] → capture is a documented,
  repeatable Playwright script (`scripts/capture-screenshots.ts`), re-run before
  releases.
- [Unapproved marketing claims] → outcomes, pricing and testimonials are content
  files that need an explicit value; the spec forbids invented figures and the
  sections render nothing when a collection is empty.
- [Monochrome looks flat] → weight comes from scale, contrast and depth: an
  ink-anchored hero and final CTA, large display type, real product imagery, and
  the `--success` saving highlight as the single accent.
- [GSAP licence] → GSAP and all its plugins have been free for commercial use since
  the Webflow acquisition (2024); recorded here so it is checked again before launch.

## Migration Plan

Additive. The new app is built and previewed locally on port 3200; deploying it to
a static host and pointing `steelyard.com` (and a `www` redirect) at it is a
separate, manual step.
Rollback is removing the deployment; nothing else depends on the site.

## Open Questions

- Outcome figures: which numbers (e.g., share of lines auto-categorized, typical
  savings found) are approved and from which source.
- Demo booking tool (Cal.com, HubSpot, …).
- The starter legal pages need a lawyer's review before the first paying customer
  signs up.
