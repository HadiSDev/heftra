## RENAMED Requirements

- FROM: `### Requirement: The product is named Steelyard`
- TO: `### Requirement: The product is named Heftra`

## MODIFIED Requirements

### Requirement: The brand source lives in the repository

The Heftra logo pack SHALL be tracked under `brand/` as the single source of
truth (SVG, PNG, favicon and social variants, and the pack's usage rules).
Assets the web app serves SHALL be copies of files in `brand/`, never edited or
re-exported variants of them. No file named after a former product name SHALL
remain in `brand/`.

#### Scenario: A served asset traces to the pack

- **WHEN** any favicon, manifest icon, or OG image under `apps/web/public` is
  compared with the file of the same role in `brand/`
- **THEN** the bytes are identical

#### Scenario: The pack carries only the current name

- **WHEN** the files under `brand/` are listed
- **THEN** every named lockup, symbol and app-icon file starts with `heftra-`,
  and none starts with `steelyard-`

### Requirement: The product is named Heftra

Every surface on which a person reads the product's name SHALL say **Heftra**.
That covers:

- the browser title;
- the web manifest (`name`, `short_name`);
- the app chrome, the sign-in page and the loading screen;
- the name of the system actor in a voucher's activity ("Heftra AI" for the
  categorizer);
- the web API's documentation title and the Streamlit dashboard title;
- the project's README and CLAUDE.md.

"Steelyard", "Spend Predictor", "ERP Procurement Agent" and "ERPSAA" SHALL NOT
appear on any of them.

#### Scenario: No legacy product name is shown

- **WHEN** these are searched case-insensitively for "steelyard",
  "spend predictor", "procurement agent" (as a product name) and "erpsaa":
  - the frontend source;
  - the web API app factory and the Streamlit dashboard;
  - README, CLAUDE.md and the living specs.
- **THEN** there are no matches

#### Scenario: The categorizer is named in activity

- **WHEN** a voucher's activity shows an event recorded by the AI categorizer
- **THEN** its headline names the actor "Heftra AI"

### Requirement: The logo is rendered from its outlines, in ink

The application SHALL render the Heftra lockup and symbol from the pack's
outlined SVG geometry through one shared `Logo` component. The lockup's
wordmark path and viewBox SHALL be those of `brand/svg/heftra-lockup-black.svg`.
The wordmark SHALL NOT be retyped as text in any font. The logo SHALL be drawn
in `currentColor` and placed only where that resolves to the ink (black on light
surfaces, white on dark). It SHALL NOT be recoloured, tinted, given effects or
gradients, tilted, or stretched.

The lockup SHALL NOT render narrower than 80 px and the symbol SHALL NOT render
smaller than 20 px. Below 32 px the symbol SHALL use the favicon geometry (the
thicker arm). Clear space around the logo SHALL be at least the diameter of the
large circle.

#### Scenario: The sidebar shows the lockup

- **WHEN** the app shell renders
- **THEN** the sidebar header shows the Heftra lockup as SVG, with an accessible
  name of "Heftra", and no text node containing the product name next to an
  icon

#### Scenario: The wordmark matches the pack

- **WHEN** the `Logo` component's wordmark path is compared with
  `brand/svg/heftra-lockup-black.svg`
- **THEN** the path data is identical

#### Scenario: The logo follows the theme

- **WHEN** the theme switches between light and dark
- **THEN** the logo is black on the light canvas and white on the dark canvas,
  with no other color

#### Scenario: Small symbol uses the favicon geometry

- **WHEN** the symbol is rendered at a size below 32 px
- **THEN** it uses the favicon variant's thicker arm

### Requirement: The web app carries the brand in its metadata

The document head SHALL link the favicon set from the pack (`favicon.ico`,
`favicon.svg`, `apple-touch-icon.png`) and declare `theme-color` `#0A0A0A`. It
SHALL declare Open Graph and Twitter card metadata using:

- the pack's `og-image-1200x630.png`;
- the name "Heftra";
- the tagline "Know the true price of everything you buy."

The web manifest SHALL reference the pack's app icons at 192 and 512 px and use
`#0A0A0A` as its theme color.

#### Scenario: Favicon and share card

- **WHEN** the app's HTML head is rendered
- **THEN** it contains the three icon links, `theme-color` `#0A0A0A`, and an
  `og:image` pointing at the OG image, with `og:title` "Heftra"

#### Scenario: Installed app icon

- **WHEN** the web manifest is read
- **THEN** its `name` and `short_name` are "Heftra" and its icons are the pack's
  192 and 512 px app icons

### Requirement: Local infrastructure carries the product name

The local development stack SHALL use `heftra` for:

- the compose project name;
- the PostgreSQL database, role and password;
- the default S3 bucket and the default dev object-store access key.

Every default connection string and storage setting in the code and in
`.env.example` SHALL use it.

An existing development stack initialised under a former name SHALL carry
across without losing data:

- a provided script SHALL rename the database and role in place;
- a documented one-time step SHALL carry the object store's named volume to the
  new compose project, or keep the old bucket and credentials through `.env`
  overrides.

#### Scenario: A fresh stack

- **WHEN** `docker compose up` initialises an empty data directory
- **THEN** a database and role named `heftra` exist, and the web API's default
  `DATABASE_URL` connects to them

#### Scenario: An existing dev database is carried across

- **WHEN** the rename script runs with its defaults against a database
  initialised as `steelyard`
- **THEN** afterwards the database and role are `heftra`, every existing table
  and row is present, and `alembic current` reports the same head

#### Scenario: An older dev database is carried across

- **WHEN** the rename script runs with `--from spend_predictor` against a
  database initialised under that name
- **THEN** afterwards the database and role are `heftra`, with every table and
  row present

## ADDED Requirements

### Requirement: The product's public origins are on heftra.com

The product's public origins SHALL be:

- `https://heftra.com` for the marketing site;
- `https://app.heftra.com` for the web app;
- `https://api.heftra.com` for the web API.

Every production default, documented production value and published contact
address SHALL use them. Contact addresses are `hello@heftra.com` and
`privacy@heftra.com`.

`heftra.ai`, `www.heftra.ai` and `www.heftra.com` SHALL permanently redirect
to the same path on `https://heftra.com`. Outside archived changes and
historical plans, no tracked file SHALL reference a `steelyard.com` host or
address.

#### Scenario: Production defaults

- **WHEN** the landing image is built with no `PUBLIC_*` overrides
- **THEN** its canonical URLs start with `https://heftra.com/`, its "Sign in"
  links point at `https://app.heftra.com/sign-in`, and its demo form posts to
  `https://api.heftra.com`

#### Scenario: Published contact addresses

- **WHEN** the built landing site is searched for email addresses on the
  product's domain
- **THEN** every match ends in `@heftra.com`

#### Scenario: No old host remains

- **WHEN** tracked files outside `openspec/changes/archive` and
  `docs/superpowers` are searched for "steelyard.com"
- **THEN** there are no matches
