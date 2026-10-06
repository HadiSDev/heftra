import { expect, test } from '@playwright/test'

test('follows a dark system preference on the first visit', async ({
  page,
}) => {
  await page.emulateMedia({ colorScheme: 'dark' })
  await page.goto('/')
  await expect(page.locator('html')).toHaveClass(/\bdark\b/)
})

test('remembers the chosen theme from the first frame', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'dark' })
  await page.goto('/privacy/')
  await page.getByRole('button', { name: 'Switch to light theme' }).click()
  await expect(page.locator('html')).not.toHaveClass(/\bdark\b/)

  await page.addInitScript(() => {
    const observer = new MutationObserver(() => {
      if (document.documentElement && !('firstThemeSeen' in window)) {
        Object.assign(window, {
          firstThemeSeen: document.documentElement.classList.contains('dark'),
        })
      }
    })
    observer.observe(document, {
      childList: true,
      subtree: true,
      attributes: true,
    })
  })
  await page.reload()
  await expect(page.locator('html')).not.toHaveClass(/\bdark\b/)
  const firstThemeWasDark = await page.evaluate(
    () => (window as unknown as { firstThemeSeen?: boolean }).firstThemeSeen,
  )
  expect(firstThemeWasDark).not.toBe(true)
})
