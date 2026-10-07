import type { ComponentType } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import { Route } from './sign-in'

const clerk = {
  password: vi.fn().mockResolvedValue({ error: null }),
  finalize: vi.fn().mockResolvedValue({ error: null }),
  sso: vi.fn(),
  emailCode: { sendCode: vi.fn(), verifyCode: vi.fn() },
  status: 'complete',
}

vi.mock('@clerk/tanstack-react-start', () => ({
  useSignIn: () => ({ signIn: clerk, fetchStatus: 'idle' }),
  useAuth: () => ({ isSignedIn: false }),
}))

vi.mock('@tanstack/react-router', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  useNavigate: () => vi.fn(),
}))

vi.mock('#/lib/env', () => ({
  GOOGLE_OAUTH_ENABLED: false,
  DEMO_LOGIN: { email: 'demo@heftra.com', password: 'open-sesame' },
}))

const SignInPage = Route.options.component as unknown as ComponentType

describe('sign-in on the hosted demo', () => {
  it('shows the shared login and prefills the password form', () => {
    render(<SignInPage />)

    expect(screen.getByRole('region', { name: 'Demo access' })).toBeTruthy()
    expect(screen.getByLabelText<HTMLInputElement>('Email').value).toBe(
      'demo@heftra.com',
    )
  })

  it('signs in as the demo user with one click', async () => {
    render(<SignInPage />)

    fireEvent.click(screen.getByRole('button', { name: 'Sign in to the demo' }))

    await waitFor(() => expect(clerk.finalize).toHaveBeenCalled())
    expect(clerk.password).toHaveBeenCalledWith({
      identifier: 'demo@heftra.com',
      password: 'open-sesame',
    })
  })
})
