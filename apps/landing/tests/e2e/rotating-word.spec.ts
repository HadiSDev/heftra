import { expect, test } from '@playwright/test'

const heading = '#product-title'

test('the currency in the product heading rolls through other currencies', async ({
  page,
}) => {
  await page.goto('/#product')
  await page.waitForFunction(() =>
    document.documentElement.classList.contains('motion-ready'),
  )
  const track = page.locator(`${heading} [data-rotating-word-track]`)
  await expect(page.locator(`${heading} .rotating-word`)).toHaveClass(
    /is-rotating/,
  )
  await expect
    .poll(
      async () =>
        track.evaluate(
          (element) => new DOMMatrix(getComputedStyle(element).transform).m42,
        ),
      {
        timeout: 6000,
      },
    )
    .toBeLessThan(0)
})

test('screen readers hear a stable heading', async ({ page }) => {
  await page.goto('/')
  await expect(
    page.getByRole('heading', {
      level: 2,
      name: 'One platform for every EUR you spend.',
    }),
  ).toBeAttached()
})

test('with reduced motion the currency changes by fading, not rolling', async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.goto('/#product')
  const root = page.locator(`${heading} .rotating-word`)
  const viewport = root.locator('.rotating-word-window')
  await expect(root).toHaveClass(/is-rotating/)
  await expect
    .poll(
      () => viewport.evaluate((element) => getComputedStyle(element).opacity),
      {
        timeout: 6000,
        intervals: [50],
      },
    )
    .not.toBe('1')
  await expect
    .poll(
      () =>
        root
          .locator('[data-rotating-word-track]')
          .evaluate(
            (element) => new DOMMatrix(getComputedStyle(element).transform).m42,
          ),
      { timeout: 6000 },
    )
    .toBeLessThan(0)
})
