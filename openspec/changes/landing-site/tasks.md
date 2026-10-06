## 1. Scaffold apps/landing

- [x] 1.1 Create `apps/landing` with `package.json` (scripts `dev --port 3200`, `build`, `preview`, `check`, `test`), `astro.config.ts` (`output: 'static'`, `@tailwindcss/vite`, `@astrojs/sitemap`, `site` from `PUBLIC_SITE_URL`), `tsconfig.json` (Astro strict), `.gitignore` and `.env.example` (local `PUBLIC_SITE_URL=http://localhost:3200` and `PUBLIC_APP_URL=http://localhost:3100`; production values `https://steelyard.com` and `https://app.steelyard.com` documented beside them)
- [x] 1.2 Declare dependencies (`astro`, `@astrojs/sitemap`, `@astrojs/check`, `tailwindcss`, `@tailwindcss/vite`, `@fontsource-variable/geist`, `@fontsource-variable/geist-mono`, `gsap`, `vitest`, `@playwright/test`, `typescript`) and have Hadi run `bun install` in `apps/landing` to create `bun.lock`
- [x] 1.3 Add the `PUBLIC_SITE_URL`, `PUBLIC_APP_URL`, `PUBLIC_API_URL` env schema in `astro.config.ts` and `src/lib/links.ts` building the sign-in, `/demo` and demo-request endpoint URLs; unit-test `links.ts`
- [x] 1.4 Copy `favicon.ico`, `favicon.svg`, `apple-touch-icon.png`, `favicon-192.png`, `favicon-512.png` and `og-image-1200x630.png` from `brand/` into `apps/landing/public`, and add a test asserting byte-equality with `brand/`
- [x] 1.5 Add `robots.txt` generation referencing the sitemap, and confirm `astro build` emits `sitemap-index.xml`

## 2. Design tokens, theme and base layout

- [x] 2.1 Write `src/styles/tokens.css` mirroring the web app's light/dark tokens plus landing display type scale, section spacing and depth tokens; add a parity test against `apps/web/src/styles.css`
- [x] 2.2 Write `src/styles/global.css` (Tailwind import, Geist fonts, `@theme inline`, focus styles, skip link) and `src/styles/motion.css` (depth layer classes, `html.motion` "from" states, reduced-motion overrides)
- [x] 2.3 Implement the theme bootstrap (inline head script applying the stored or system theme before first paint) and `ThemeToggle` with per-visitor storage wrapped in try/catch
- [x] 2.4 Build `src/layouts/BaseLayout.astro` with `lang="en"`, title/description/canonical props, favicon links, `theme-color` `#0A0A0A`, Open Graph and Twitter tags, skip link, header, `main` landmark and footer
- [x] 2.5 Add `src/lib/seo.ts` with JSON-LD builders for `Organization`, `SoftwareApplication` and `FAQPage`, with unit tests

## 3. Brand and UI primitives

- [x] 3.1 Create `components/brand/Lockup.astro` and `Symbol.astro` from `brand/svg` path data in `currentColor` with `role="img"` and `aria-label="Steelyard"`, switching to favicon geometry below 32 px; add a path-parity test against `brand/svg`
- [x] 3.2 Create `components/ui/Button.astro` (primary/secondary/ghost, link-based), `Badge.astro`, `SectionHeading.astro` (eyebrow, title, lead) and `ProductFrame.astro` (window chrome around a `<Picture>`)
- [x] 3.3 Create `components/ui/FeatureBlock.astro` and `PricingCard.astro`

## 4. Content collections

- [x] 4.1 Define `src/content.config.ts` Zod schemas for `features`, `integrations`, `outcomes`, `pricing`, `faq` and `testimonials`, including `draft` on outcomes
- [x] 4.2 Add a build-time check that fails a production build on any `draft: true` outcome and names it, and a dev-only "Draft" marker
- [x] 4.3 Write the content: six features from shipped capabilities, integrations (enterprise ERPs first: Dynamics 365, SAP, Oracle NetSuite, IFS Cloud and Visma.net coming soon; Billy last as the live connector), an empty outcomes file until figures are approved, the three plans from the design (Business, Group, Enterprise) with monthly/annual prices, 8–10 FAQ entries, empty testimonials
- [x] 4.4 Write the starter privacy policy and terms of service from the outlines in the design, each with a "Last updated" date

## 5. Product imagery

- [x] 5.1 Write `apps/landing/scripts/capture-screenshots.ts` (Playwright, Clerk impersonation on dev, 2× scale, light and dark) for dashboard, spend lines, alternatives, agreement compliance, suppliers and emissions
- [x] 5.2 Run the capture against the local web app with seeded demo data (the fictional "Nordlys Byg A/S" from `apps/ai-api/scripts/demo_company`), with dev overlays hidden and the signed-in person and organization replaced by a persona, and commit the images under `src/assets/product/`
- [x] 5.3 Inspect the captures and assign their roles: full-UI screenshots keep their backgrounds (they are content, not cut-outs); the dashboard is the hero asset at depth 3, feature and step screens sit in framed depth-3 visuals

## 6. Layout components

- [x] 6.1 Build `components/layout/Header.astro` (sticky, lockup, anchor links, Sign in, Get a demo, theme toggle) with offset scrolling so anchored headings clear the header
- [x] 6.2 Build `components/layout/MobileMenu.astro` with `aria-expanded`, focus moving into the menu, Escape to close and focus returning to the button
- [x] 6.3 Build `components/layout/Footer.astro` (lockup, product/company/legal columns, contact email, current-year copyright)

## 7. Home page sections

- [x] 7.1 `Hero.astro`: ink canvas in both themes, depth 0–5 layers (grid, glow, companion chips, framed dashboard, copy and CTAs, particles), one `h1`, decorative layers `aria-hidden`
- [x] 7.2 `Integrations.astro`: ERP strip from the integrations collection with Live / Coming soon badges
- [x] 7.3 `Problem.astro`: problem statement paragraph prepared for word-by-word lighting, three pain points
- [x] 7.4 `HowItWorks.astro` (`#how-it-works`): three steps with their screenshots, authored as a plain sequential layout that the motion script turns into a pinned scene
- [x] 7.5 `Features.astro` (`#product`): one `FeatureBlock` per feature entry, alternating image side
- [x] 7.6 `Outcomes.astro`: figures from the outcomes collection, rendering nothing when empty
- [x] 7.7 `Security.astro` (`#security`): EU residency, tenant isolation, encrypted credentials, human review and human-correction precedence
- [x] 7.8 `Testimonials.astro`: renders only when the collection has entries
- [x] 7.9 `Pricing.astro` (`#pricing`): plan cards, recommended plan, monthly/annual toggle when both are defined, keyboard-operable
- [x] 7.10 `Faq.astro` (`#faq`): `<details>/<summary>` list from the FAQ collection plus `FAQPage` JSON-LD from the same entries
- [x] 7.11 `FinalCta.astro`: ink-anchored closing section mirroring the hero
- [x] 7.12 Compose `pages/index.astro` in the spec's section order with `Organization` and `SoftwareApplication` JSON-LD

## 8. Supporting pages

- [x] 8.1 `pages/privacy.astro` and `pages/terms.astro` on the base layout with unique titles and descriptions
- [x] 8.2 `pages/404.astro` with the lockup and a link home
- [x] 8.3 `pages/demo.astro` with `components/demo/DemoForm.astro` (labelled fields, company-size select, consent linking `/privacy`, hidden honeypot, `rendered_at`) and a `<noscript>` contact fallback
- [x] 8.4 `scripts/demo-form.ts`: post JSON to the demo-request endpoint, map 422 field errors onto fields with `aria-describedby` and focus the first, show a generic error with the contact email otherwise, and replace the form with a live-region confirmation and the returned "Choose a time" link

## 9. Motion

- [x] 9.1 `scripts/motion/index.ts`: run only on `prefers-reduced-motion: no-preference`, add the `motion` class to `<html>`, register ScrollTrigger, and detect coarse pointers
- [x] 9.2 `depth-parallax.ts`: per-depth parallax and the hero float loop, companion chips scattering on scroll-out, reduced distances on coarse pointers
- [x] 9.3 `text-reveals.ts`: masked line reveals on section headings and word-by-word lighting in the Problem section
- [x] 9.4 `pinned-steps.ts`: pinned How-it-works scene with scrub timeline, screenshot crossfade and clip-path wipe; no pinning on coarse pointers
- [x] 9.5 `stagger-grid.ts` and `counters.ts`: staggered feature/pricing/outcome entrances, window-pane iris on feature images, outcome count-up
- [x] 9.6 Clear `will-change` after each tween completes and confirm only `transform`, `opacity`, `filter` and `clip-path` are animated
- [x] 9.7 `rotating-words.ts`: roll the currency in the Product heading through other currencies, stable accessible name, a crossfade instead of a roll with reduced motion

## 10. Verification

- [x] 10.1 Built-output tests over `dist/`: one `h1`, the five anchors, header/nav/footer, absolute `og:image` with "Steelyard" title and tagline, sitemap lists all pages, no testimonials heading when empty, no legacy product names, Sign in links use `PUBLIC_APP_URL`, Get a demo CTAs go to `/demo`, no `/sign-up` link exists, and the booking URL appears nowhere in `dist/`
- [x] 10.2 Test that a production build without `PUBLIC_SITE_URL` fails naming the variable
- [x] 10.3 Playwright smoke tests against `astro preview`: mobile menu keyboard flow at 375 px, theme persistence without flash, reduced-motion and no-JS runs leave all content visible, Pricing nav link lands on the heading
- [ ] 10.4 Run Lighthouse (mobile) on the built home page; meet ≥ 90 in all four categories and CLS < 0.1, and fix any failures
- [x] 10.5 Check contrast for both themes and visible focus on every interactive element
- [x] 10.6 Run `astro check`, the Vitest suite and the epic-design `validate-layers.js` on the built home page; all pass

- [x] 10.7 SEO pass: titles ≤ 60 and descriptions ≤ 160 characters, robots directives, `noindex` 404, trailing-slash internal links, `WebSite`/`BreadcrumbList` JSON-LD and per-plan offers, `og:locale`, font preload, web manifest, sitemap `lastmod`, `llms.txt`, with build tests

## 11. Repository updates

- [x] 11.1 Add a Landing section to the root README (what it is, `cd apps/landing && bun run dev` on port 3200, env vars) and an `apps/landing/README.md`
- [x] 11.2 Update CLAUDE.md or infra notes where the app list or dev ports are enumerated

## 12. Demo requests in web-api

- [x] 12.1 Add `DEMO_BOOKING_URL` and `DEMO_REQUEST_RATE_LIMIT` to `web_api/config.py` and `.env.example`, and add `http://localhost:3200` to the documented `WEB_API_CORS_ORIGINS`
- [x] 12.2 Add `db/models/demo_request.py` (global `demo_requests` table), export it from `db/models/__init__.py`, and write migration `0025_demo_requests`
- [x] 12.3 Add `schemas/demo_requests.py` with the request (pattern-validated email, size enum, consent must be true, message length cap, honeypot, `rendered_at`) and response models
- [x] 12.4 Add `web_api/demo_requests/guard.py` with the honeypot / minimum-fill-time check and the per-IP sliding-window rate limiter
- [x] 12.5 Add `routers/public_demo_requests.py` (`POST /api/v1/public/demo-requests`, no auth) and register it in `app.py`
- [x] 12.6 Tests in `tests/api/test_public_demo_requests.py`: stores a valid request and returns the booking URL without auth, 422 on bad email / missing consent / unknown size, honeypot and too-fast submits return 201 without storing or returning the link, 429 after the limit, null booking URL when unset
