import { expect, test } from '@playwright/test'

test.describe('mobile menu', () => {
  test.use({ viewport: { width: 375, height: 812 } })

  test('opens, moves focus in, and closes on Escape', async ({ page }) => {
    await page.goto('/')
    const button = page.getByRole('button', { name: 'Open menu' })
    await button.click()

    await expect(
      page.getByRole('button', { name: 'Close menu' }),
    ).toHaveAttribute('aria-expanded', 'true')
    await expect(page.locator('#mobile-menu-panel')).toBeVisible()
    await expect(page.locator('#mobile-menu-panel a').first()).toBeFocused()

    await page.keyboard.press('Escape')
    await expect(page.locator('#mobile-menu-panel')).toBeHidden()
    await expect(page.getByRole('button', { name: 'Open menu' })).toBeFocused()
  })
})

test('the Pricing link lands on the pricing heading below the header', async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.goto('/')
  await page
    .getByRole('navigation', { name: 'Main' })
    .getByRole('link', { name: 'Pricing' })
    .click()
  await expect(page).toHaveURL(/#pricing$/)

  const heading = page.locator('#pricing-title')
  const headerBottom = await page
    .locator('[data-header-nav]')
    .evaluate((nav) => nav.getBoundingClientRect().bottom)
  const headingTop = await heading.evaluate(
    (element) => element.getBoundingClientRect().top,
  )
  expect(headingTop).toBeGreaterThan(headerBottom)
  await expect(heading).toBeInViewport()
})

test('the FAQ opens from the keyboard', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.goto('/#faq')
  const question = page.locator('#faq summary').first()
  await question.focus()
  await page.keyboard.press('Enter')
  await expect(page.locator('#faq details').first()).toHaveAttribute('open', '')
})

test('the billing toggle switches to yearly prices', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.goto('/#pricing')
  const firstMonthly = page.locator('#pricing .price-monthly').first()
  const firstAnnual = page.locator('#pricing .price-annual').first()
  await expect(firstMonthly).toBeVisible()
  await expect(firstAnnual).toBeHidden()

  await page.locator('#pricing label', { hasText: 'Yearly' }).click()
  await expect(firstAnnual).toBeVisible()
  await expect(firstMonthly).toBeHidden()
})

test.describe('phone width', () => {
  test.use({ viewport: { width: 375, height: 812 } })

  for (const path of ['/', '/demo/', '/privacy/', '/terms/']) {
    test(`${path} has no horizontal scroll`, async ({ page }) => {
      await page.emulateMedia({ reducedMotion: 'reduce' })
      await page.goto(path)
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - window.innerWidth,
      )
      expect(overflow).toBeLessThanOrEqual(0)
    })
  }
})
