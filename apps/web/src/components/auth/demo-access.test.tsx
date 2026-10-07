import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import { DemoAccess } from './demo-access'

const login = { email: 'demo@heftra.com', password: 'open-sesame' }

describe('DemoAccess', () => {
  it('shows the shared login', () => {
    render(<DemoAccess login={login} onSignIn={vi.fn()} />)

    expect(screen.getByRole('region', { name: 'Demo access' })).toBeTruthy()
    expect(screen.getByText('demo@heftra.com')).toBeTruthy()
    expect(screen.getByText('open-sesame')).toBeTruthy()
  })

  it('signs in with one click and shows progress meanwhile', async () => {
    let release: () => void = () => undefined
    const onSignIn = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          release = resolve
        }),
    )
    render(<DemoAccess login={login} onSignIn={onSignIn} />)

    fireEvent.click(screen.getByRole('button', { name: 'Sign in to the demo' }))

    expect(onSignIn).toHaveBeenCalledOnce()
    expect(screen.getByRole('button', { name: 'Signing in…' })).toBeTruthy()
    release()
    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: 'Sign in to the demo' }),
      ).toBeTruthy(),
    )
  })
})
