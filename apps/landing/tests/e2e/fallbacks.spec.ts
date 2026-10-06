import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'

async function expectEverythingVisible(page: Page): Promise<void> {
  const hidden = await page.evaluate(() => {
    const selectors =
      'main h1, main h2:not(.visually-hidden), main h3, main p:not(.visually-hidden), main a, main img'
    return Array.from(document.querySelectorAll<HTMLElement>(selectors))
      .filter(
        (element) =>
          !element.closest(
            '[hidden], noscript, .honeypot, details:not([open])',
          ),
      )
      .filter((element) => {
        const style = getComputedStyle(element)
        return (
          style.visibility === 'hidden' ||
          Number(style.opacity) < 0.99 ||
          style.display === 'none'
        )
      })
      .filter(
        (element) =>
          !element.closest(
            '[data-demo-form-root] form.hidden, [data-demo-confirmation].hidden',
          ),
      )
      .map((element) => element.outerHTML.slice(0, 120))
  })
  expect(hidden).toEqual([])
}

test('reduced motion shows every section in its final state, unpinned', async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.goto('/')
  await expectEverythingVisible(page)
  await expect(page.locator('[data-how-track]')).not.toHaveClass(/is-pinned/)
  const transformed = await page
    .locator('[data-reveal]')
    .evaluateAll(
      (elements) =>
        elements.filter(
          (element) => getComputedStyle(element).transform !== 'none',
        ).length,
    )
  expect(transformed).toBe(0)
})

test.describe('without JavaScript', () => {
  test.use({ javaScriptEnabled: false })

  test('every heading, paragraph and link is visible', async ({ page }) => {
    await page.goto('/')
    await expectEverythingVisible(page)
  })

  test('the demo page offers the contact email instead of the form', async ({
    page,
  }) => {
    await page.goto('/demo/')
    await expect(
      page.getByRole('link', { name: 'hello@heftra.com' }).first(),
    ).toBeVisible()
  })
})

test('with motion, revealed content ends up fully visible', async ({
  page,
}) => {
  await page.goto('/')
  await page.waitForFunction(() =>
    document.documentElement.classList.contains('motion-ready'),
  )
  const height = await page.evaluate(() => document.body.scrollHeight)
  for (let y = 0; y < height; y += 500) {
    await page.mouse.wheel(0, 500)
    await page.waitForTimeout(60)
  }
  await page.waitForTimeout(1500)
  const stillHidden = await page
    .locator('[data-reveal="rise"], [data-reveal="fade"]')
    .evaluateAll(
      (elements) =>
        elements.filter(
          (element) => Number(getComputedStyle(element).opacity) < 0.99,
        ).length,
    )
  expect(stillHidden).toBe(0)
  const displacedLines = await page
    .locator('.reveal-line > span')
    .evaluateAll(
      (spans) =>
        spans.filter(
          (span) => new DOMMatrix(getComputedStyle(span).transform).m42 !== 0,
        ).length,
    )
  expect(displacedLines).toBe(0)
})
