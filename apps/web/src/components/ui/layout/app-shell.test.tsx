import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { APP_SCROLL_ID, AppShell } from './app-shell'

describe('AppShell', () => {
  it('fits the screen and scrolls only its content', () => {
    const { container } = render(
      <AppShell sidebar={<aside>Nav</aside>} header={<header>Top</header>}>
        <p>Page</p>
      </AppShell>,
    )

    const shell = container.firstElementChild
    expect(shell?.className).toContain('h-dvh')
    expect(shell?.className).toContain('overflow-hidden')
    const main = screen.getByRole('main')
    expect(main.id).toBe(APP_SCROLL_ID)
    expect(main.dataset.scrollRestorationId).toBe(APP_SCROLL_ID)
    expect(main.className).toContain('overflow-y-auto')
    expect(main.contains(screen.getByText('Page'))).toBe(true)
    expect(main.contains(screen.getByText('Nav'))).toBe(false)
  })
})
