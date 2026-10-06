## ADDED Requirements

### Requirement: The landing site is a static Astro app in apps/landing

The public marketing site SHALL be an Astro project in `apps/landing` with its own
`package.json`, bun lockfile and scripts (`dev`, `build`, `preview`, `check`,
`test`). It SHALL build to static HTML (`output: 'static'`) with no server runtime
and no backend calls. The dev server SHALL listen on port 3200. Styling SHALL use
Tailwind CSS v4 through its Vite plugin, and type checking SHALL pass under
`astro check`.

#### Scenario: Static build

- **WHEN** `./node_modules/.bin/astro build` runs in `apps/landing`
- **THEN** it exits 0 and writes `dist/index.html`, `dist/demo/index.html`, `dist/privacy/index.html`,
  `dist/terms/index.html`, `dist/404.html`, `dist/sitemap-index.xml` and
  `dist/robots.txt`, and `dist` contains no server entry point

#### Scenario: Dev port

- **WHEN** the dev script starts
- **THEN** the site is served on `http://localhost:3200`

### Requirement: Calls to action are configured, not hard-coded

The site SHALL read the canonical site origin from `PUBLIC_SITE_URL`, the web
app's base URL from `PUBLIC_APP_URL`, and the web API's base URL from
`PUBLIC_API_URL`. "Sign in" links SHALL point to the web app's sign-in route
under `PUBLIC_APP_URL`. Every "Get a demo" CTA SHALL link to the site's own
`/demo` page. The site SHALL NOT link to a sign-up route, promise a self-serve
free trial, or contain the demo booking URL anywhere in its built output. An
`.env.example` SHALL document all three with local defaults. The build SHALL fail
when any of them is missing.

#### Scenario: CTA targets

- **WHEN** the site is built with `PUBLIC_APP_URL=https://app.heftra.com`
- **THEN** every "Sign in" link's `href` is `https://app.heftra.com/sign-in`,
  every "Get a demo" CTA's `href` is `/demo`, and no `href` contains `/sign-up`

#### Scenario: Missing configuration

- **WHEN** a production build runs without `PUBLIC_SITE_URL`
- **THEN** the build fails with a message naming the missing variable

### Requirement: The home page has the full set of SaaS landing sections

The home page SHALL render, in order, these sections, each as its own component
with a stable anchor id where it is a navigation target:

1. **Navigation** — sticky header with the Heftra lockup, links to Product,
   How it works, Security, Pricing and FAQ, a "Sign in" link and a "Get a demo"
   button; on narrow viewports the links collapse into an accessible menu.
2. **Hero** — a single `h1` stating the value proposition, a supporting line, a
   primary CTA ("Get a demo") and a secondary CTA ("See how it works"), and a product
   visual of the web app.
3. **Integrations strip** — the ERP systems Heftra connects to, each shown
   with the vendor's official, unmodified logo and marked "Live" or "Coming
   soon" according to whether a connector ships.
4. **Problem** — why spend is opaque today (uncategorized ledger lines, duplicate
   suppliers, prices drifting from agreements).
5. **How it works** (`#how-it-works`) — three steps: connect your ERP, AI
   categorizes every line against your own spend tree, act on savings.
6. **Features** (`#product`) — one block per shipped capability: spend
   categorization, spend dashboard, cheaper alternatives, agreement compliance,
   supplier directory, spend-based emissions; each with a title, a one-sentence
   benefit, and a product image or illustration.
7. **Outcomes** — measurable results, stated only with figures the team has
   approved in the content file.
8. **AI you can trust / Security** (`#security`) — EU data residency, per-company
   tenant isolation, encrypted ERP credentials, humans review and override every
   AI decision, AI output never overwrites a human's correction.
9. **Testimonials** — rendered only when the testimonials content collection has
   at least one entry.
10. **Pricing** (`#pricing`) — plan cards from the pricing content file, one
    marked as recommended, each with a CTA; a monthly/annual toggle when the
    content defines both.
11. **FAQ** (`#faq`) — questions and answers from the FAQ content file as an
    accessible disclosure list.
12. **Final CTA** — a closing headline with the primary and secondary CTAs.
13. **Footer** — the lockup, product/company/legal link columns, contact email,
    and the copyright line with the current year.

#### Scenario: Every section is present

- **WHEN** `dist/index.html` is parsed
- **THEN** it contains exactly one `h1`, the anchors `#product`, `#how-it-works`,
  `#security`, `#pricing` and `#faq`, a `header` with a `nav`, and a `footer`

#### Scenario: Navigation reaches its anchors

- **WHEN** a visitor clicks "Pricing" in the navigation
- **THEN** the page scrolls to `#pricing` with the section heading visible below
  the sticky header

#### Scenario: Mobile menu

- **WHEN** the viewport is 375 px wide and the menu button is activated
- **THEN** the navigation links are shown, the button reports `aria-expanded="true"`,
  focus moves into the menu, and Escape closes it and returns focus to the button

### Requirement: Marketing content is truthful and lives in content files

The site SHALL keep section copy that changes independently of layout (features,
integrations, outcomes, pricing, FAQ, testimonials) in typed Astro content
collections or data files validated by a schema. The site SHALL NOT contain
invented customers, customer logos, quotes, ratings, user counts or outcome
figures. An integration SHALL be marked "Live" only when a connector for it ships
in the product.

#### Scenario: No testimonials yet

- **WHEN** the testimonials collection is empty
- **THEN** the home page renders no testimonials section and no heading for it

#### Scenario: Invalid content

- **WHEN** a pricing entry is missing its price or CTA label
- **THEN** the build fails with a schema validation error naming the entry

#### Scenario: Draft content blocks a production build

- **WHEN** an outcome entry has `draft: true` and a production build runs
- **THEN** the build fails naming the draft entry, while the dev server renders it
  with a visible "Draft" marker

#### Scenario: Integration status

- **WHEN** the integrations strip renders
- **THEN** the enterprise ERPs (Dynamics 365, SAP, Oracle NetSuite, IFS Cloud,
  Visma.net) come first, Billy is listed last and marked "Live", and every ERP
  without a shipped connector is
  marked "Coming soon"

### Requirement: The demo is booked through a free request form

The site SHALL serve a `/demo` page with a demo request form: full name, work
email, company, company size (a fixed set of ranges), an optional message, and a
required consent checkbox linking to the privacy policy. The form SHALL also carry
a visually hidden honeypot field and the time the form was rendered. On submit
the page SHALL post the request as JSON to
`${PUBLIC_API_URL}/api/v1/public/demo-requests` and, on success, replace the form
with a confirmation that shows the booking link returned by the API. Field errors
returned by the API SHALL be shown next to their fields; any other failure SHALL
show a message with the contact email. Without JavaScript the page SHALL show the
contact email instead of a form that cannot submit.

#### Scenario: Successful request

- **WHEN** a visitor fills every required field, ticks consent and submits
- **THEN** the form is replaced by a confirmation, and a "Choose a time" link to the
  booking URL from the API response is shown

#### Scenario: Booking link is gated

- **WHEN** the built site is searched for the configured booking URL
- **THEN** there are no matches; the link is only ever received from the API

#### Scenario: Invalid email

- **WHEN** the API rejects the email as invalid
- **THEN** the email field is marked invalid with the API's message, focus moves to
  it, and the other fields keep their values

#### Scenario: Accessible form

- **WHEN** the form is used with a keyboard and a screen reader
- **THEN** every field has a visible label, required fields are announced as
  required, errors are linked with `aria-describedby`, and the confirmation is
  announced through a live region

### Requirement: Supporting pages

The site SHALL serve a privacy policy at `/privacy`, terms of service at `/terms`,
and a branded 404 page that links back to the home page. All pages SHALL share one
base layout with the navigation and footer.

#### Scenario: Demo page is linked from every CTA

- **WHEN** a visitor activates "Get a demo" anywhere on the site
- **THEN** the `/demo` page opens

#### Scenario: Unknown path

- **WHEN** the static host serves a path that does not exist
- **THEN** the 404 page is shown with the Heftra lockup and a link to `/`

### Requirement: Cinematic motion with a full reduced-motion fallback

The home page SHALL use scroll-driven motion: a layered hero with depth parallax
and a floating product visual, text reveals on section headings, a pinned
"How it works" sequence that advances through the three steps as the visitor
scrolls, and staggered entrances for feature and pricing cards. Motion SHALL
animate only `transform`, `opacity`, `filter` and `clip-path`. Decorative layers
SHALL carry `aria-hidden="true"`.

When the visitor prefers reduced motion, or JavaScript is unavailable, every
section SHALL render in its final, fully visible state with no pinning, parallax
or scroll-triggered animation. On coarse pointers parallax depth SHALL be reduced
and pinning disabled.

#### Scenario: Reduced motion

- **WHEN** the page loads with `prefers-reduced-motion: reduce`
- **THEN** no element has an animated transform, the "How it works" steps are
  laid out one after another without pinning, and all text is visible

#### Scenario: Rolling currency

- **WHEN** the Product heading is in view with motion allowed
- **THEN** the currency code "EUR" in "every EUR you spend" rolls through other
  currency codes (DKK, SEK, NOK, PLN, GBP, CHF, USD) and back, the heading's
  accessible name stays "One platform for every EUR you spend.", and with reduced motion the word changes by a crossfade
  instead of rolling

#### Scenario: No JavaScript

- **WHEN** the page loads with JavaScript disabled
- **THEN** every heading, paragraph, image and CTA is visible and every link works

#### Scenario: No layout shift

- **WHEN** Lighthouse runs against the built home page on mobile
- **THEN** Cumulative Layout Shift is below 0.1

### Requirement: The site is accessible and fast

Pages SHALL meet WCAG 2.1 AA: text contrast of at least 4.5:1 (3:1 for large
text) in both themes, visible focus on every interactive element, a skip link to
the main content, landmark regions, meaningful `alt` text on product images and
empty `alt` on decorative ones, and full keyboard operation of the menu, pricing
toggle and FAQ. Images SHALL be served through Astro's image pipeline in modern
formats with explicit dimensions, below-the-fold images lazy-loaded. JavaScript
SHALL load only for interactive islands and the motion script.

#### Scenario: Lighthouse budget

- **WHEN** Lighthouse runs against the built home page on mobile
- **THEN** Performance, Accessibility, Best Practices and SEO each score at least 90

#### Scenario: Keyboard-only FAQ

- **WHEN** a keyboard user tabs to an FAQ question and presses Enter
- **THEN** the answer expands and the control reports `aria-expanded="true"`

### Requirement: The site follows the visitor's theme

The site SHALL render a light and a dark theme from the same monochrome tokens as
the web app (canvas, foreground, muted, border; ink `#0A0A0A` and white), choose
the theme from `prefers-color-scheme` on first visit, offer a toggle in the
navigation, and remember the choice per visitor. The stored choice SHALL be
applied before first paint so the page never flashes the other theme.

#### Scenario: Dark preference

- **WHEN** a first-time visitor's system prefers dark
- **THEN** the page renders on the `#0A0A0A` canvas with the white lockup

#### Scenario: Remembered choice

- **WHEN** a visitor switches to light and reloads
- **THEN** the page paints in light from the first frame

### Requirement: Search and sharing metadata

Every page SHALL set a unique `<title>` and meta description, a canonical URL
under `PUBLIC_SITE_URL`, Open Graph and Twitter card tags using the brand pack's
OG image, and `lang="en"`. The build SHALL emit a sitemap of all pages and a
`robots.txt` that references it. The home page SHALL embed JSON-LD for the
`Organization` and the `SoftwareApplication`, and the FAQ section SHALL embed
`FAQPage` JSON-LD generated from the same FAQ content.

Titles SHALL be at most 60 characters and meta descriptions 70 to 160
characters. Indexable pages SHALL declare `index, follow` with large image
previews; the 404 page SHALL be `noindex` and carry no canonical link. Internal
links SHALL use the canonical trailing-slash form of each page. The home page
SHALL also embed `WebSite` JSON-LD and list one EUR `Offer` per priced plan in its
`SoftwareApplication` data, and every other page SHALL embed a `BreadcrumbList`
back to the home page. The sitemap SHALL stamp entries with `lastmod`, the site
SHALL serve a web manifest and an `llms.txt` summary generated from the same
content collections, and the headline font SHALL be preloaded.

#### Scenario: Snippet lengths

- **WHEN** the built pages are parsed
- **THEN** every indexable page's title is at most 60 characters and its
  description is 70 to 160 characters

#### Scenario: Error page stays out of the index

- **WHEN** `dist/404.html` is parsed
- **THEN** it declares `noindex, follow` and has no canonical link

#### Scenario: Internal links need no redirect

- **WHEN** the links on any page are collected
- **THEN** every internal page link ends in `/` (before any `#fragment`)

#### Scenario: Summary for AI assistants

- **WHEN** `/llms.txt` is requested
- **THEN** it describes Heftra and lists its features, ERP integrations, plans
  and FAQ from the content collections

#### Scenario: Share card

- **WHEN** the home page's head is parsed
- **THEN** `og:title` is "Heftra", `og:description` contains "Know the true
  price of everything you buy.", and `og:image` is an absolute URL to
  `og-image-1200x630.png`

#### Scenario: Production canonical URLs

- **WHEN** the site is built with `PUBLIC_SITE_URL=https://heftra.com`
- **THEN** the home page's canonical link is `https://heftra.com/`, `/privacy`
  has `https://heftra.com/privacy`, and every sitemap entry starts with
  `https://heftra.com/`

#### Scenario: FAQ structured data matches the page

- **WHEN** the FAQ content has N entries
- **THEN** the `FAQPage` JSON-LD has N `mainEntity` items with the same questions
