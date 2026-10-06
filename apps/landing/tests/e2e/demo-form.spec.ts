import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'

const endpoint = '**/api/v1/public/demo-requests'

async function fillValidForm(page: Page): Promise<void> {
  await page.getByRole('textbox', { name: 'Full name' }).fill('Mette Hansen')
  await page
    .getByRole('textbox', { name: 'Work email' })
    .fill('mette@example.dk')
  await page
    .getByRole('textbox', { name: 'Company', exact: true })
    .fill('Nordisk Byg ApS')
  await page
    .getByRole('combobox', { name: 'Company size' })
    .selectOption('50-249')
  await page.getByRole('checkbox').check()
}

test('a valid request shows the booking link from the API', async ({
  page,
}) => {
  let body: Record<string, unknown> = {}
  await page.route(endpoint, async (route) => {
    body = route.request().postDataJSON()
    await route.fulfill({
      status: 201,
      json: { booking_url: 'https://booking.example/steelyard' },
    })
  })
  await page.goto('/demo/')
  await fillValidForm(page)
  await page.getByRole('button', { name: 'Request my demo' }).click()

  await expect(
    page.getByRole('heading', { name: 'Thanks, your request is in.' }),
  ).toBeVisible()
  await expect(
    page.getByRole('link', { name: 'Choose a time' }),
  ).toHaveAttribute('href', 'https://booking.example/steelyard')
  expect(body).toMatchObject({
    company_size: '50-249',
    consent: true,
    website: '',
  })
  expect(typeof body.rendered_at).toBe('number')
})

test('server field errors appear next to their field and take focus', async ({
  page,
}) => {
  await page.route(endpoint, (route) =>
    route.fulfill({
      status: 422,
      json: {
        detail: [
          {
            loc: ['body', 'email'],
            msg: 'Value error, Enter a valid email address',
          },
        ],
      },
    }),
  )
  await page.goto('/demo/')
  await fillValidForm(page)
  await page.getByRole('button', { name: 'Request my demo' }).click()

  const email = page.getByRole('textbox', { name: 'Work email' })
  await expect(email).toHaveAttribute('aria-invalid', 'true')
  await expect(email).toBeFocused()
  await expect(page.locator('#demo-email-error')).toHaveText(
    'Enter a valid email address',
  )
  await expect(page.getByRole('textbox', { name: 'Full name' })).toHaveValue(
    'Mette Hansen',
  )
})

test('missing consent is caught before sending', async ({ page }) => {
  let requests = 0
  await page.route(endpoint, (route) => {
    requests += 1
    return route.fulfill({ status: 201, json: { booking_url: null } })
  })
  await page.goto('/demo/')
  await fillValidForm(page)
  await page.getByRole('checkbox').uncheck()
  await page.getByRole('button', { name: 'Request my demo' }).click()

  await expect(page.locator('#demo-consent-error')).toBeVisible()
  expect(requests).toBe(0)
})

test('without a booking link the visitor is told we will email them', async ({
  page,
}) => {
  await page.route(endpoint, (route) =>
    route.fulfill({ status: 201, json: { booking_url: null } }),
  )
  await page.goto('/demo/')
  await fillValidForm(page)
  await page.getByRole('button', { name: 'Request my demo' }).click()

  await expect(
    page.getByText('We will email you within one business day'),
  ).toBeVisible()
  await expect(page.getByRole('link', { name: 'Choose a time' })).toBeHidden()
})
