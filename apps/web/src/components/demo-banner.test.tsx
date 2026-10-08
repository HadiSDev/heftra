import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { DemoBanner } from './demo-banner'

const principal = { demo: false }

vi.mock('#/lib/auth/auth', () => ({
  usePrincipal: () => principal,
}))

afterEach(() => {
  cleanup()
})

describe('DemoBanner', () => {
  it('tells a demo visitor their changes are not saved', () => {
    principal.demo = true
    render(<DemoBanner />)

    expect(screen.getByRole('status').textContent).toMatch(
      /changes aren’t saved, and the demo resets every night/,
    )
  })

  it('renders nothing for anyone else', () => {
    principal.demo = false
    const { container } = render(<DemoBanner />)

    expect(container.innerHTML).toBe('')
  })
})
