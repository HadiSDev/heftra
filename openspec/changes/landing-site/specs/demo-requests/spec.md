## ADDED Requirements

### Requirement: Visitors can request a demo without an account

The web API SHALL accept `POST /api/v1/public/demo-requests` without
authentication. The body SHALL carry `name`, `email`, `company`, `company_size`
(one of `1-49`, `50-249`, `250-999`, `1000+`), an optional `message` of at most
2,000 characters, `consent` (which MUST be `true`), a honeypot field `website`,
and `rendered_at` (the time the form was shown, epoch milliseconds). A valid
request SHALL be stored as a `DemoRequest` with the consent time, the client IP
and user agent, and SHALL be answered with `201` and
`{"booking_url": <DEMO_BOOKING_URL>}`, or `{"booking_url": null}` when that
setting is empty.

#### Scenario: A valid request

- **WHEN** a request with every required field and `consent: true` is posted with
  no `Authorization` header, more than 3 seconds after `rendered_at`
- **THEN** the response is `201` with the configured booking URL, and one
  `demo_requests` row holds the submitted values and a `consented_at` timestamp

#### Scenario: Booking link not configured

- **WHEN** `DEMO_BOOKING_URL` is empty and a valid request is posted
- **THEN** the response is `201` with `booking_url: null` and the request is stored

### Requirement: Invalid demo requests are rejected with field errors

The endpoint SHALL answer `422` with field-level errors when the email is not a
valid address, a required field is blank, the company size is not one of the
allowed ranges, the message is too long, or consent is not `true`. Nothing SHALL be
stored for a rejected request.

#### Scenario: Missing consent

- **WHEN** a request is posted with `consent: false`
- **THEN** the response is `422` naming the `consent` field and no row is stored

#### Scenario: Malformed email

- **WHEN** a request is posted with `email: "not-an-email"`
- **THEN** the response is `422` naming the `email` field

### Requirement: Automated submissions are absorbed silently

The endpoint SHALL answer a request whose honeypot field is non-empty, or that
arrives less than 3 seconds after `rendered_at`, with `201` and
`booking_url: null`, and SHALL NOT store it. The response SHALL NOT reveal that it was discarded.

#### Scenario: Honeypot filled

- **WHEN** a request is posted with `website: "https://spam.example"`
- **THEN** the response is `201` with `booking_url: null` and no row is stored

#### Scenario: Submitted too fast

- **WHEN** a request is posted 500 ms after its `rendered_at`
- **THEN** the response is `201` with `booking_url: null` and no row is stored

### Requirement: Demo requests are rate-limited per client

The endpoint SHALL allow at most `DEMO_REQUEST_RATE_LIMIT` requests (default 5)
per client IP in a sliding one-hour window, and SHALL answer further requests
with `429` and a `Retry-After` header.

#### Scenario: Over the limit

- **WHEN** the same client posts a sixth request within an hour under the default
  limit
- **THEN** the response is `429` with `Retry-After`, and no sixth row is stored

### Requirement: The landing site may call the endpoint from the browser

The web API SHALL allow cross-origin requests from the landing site's origin when
that origin is listed in `WEB_API_CORS_ORIGINS`, and the documented local value
SHALL include `http://localhost:3200`.

#### Scenario: Preflight from the landing site

- **WHEN** the browser sends a CORS preflight from `http://localhost:3200` for
  `POST /api/v1/public/demo-requests` and that origin is configured
- **THEN** the response allows the origin and the `POST` method
