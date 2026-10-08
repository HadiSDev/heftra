import type { ComponentType } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'
import { ToastProvider } from '#/components/ui'
import type * as AuthModule from '#/lib/auth/auth'
import type { Principal } from '#/lib/auth/auth'
import { DEMO_REFUSAL } from '#/lib/api/demo-refusal'
import { DEMO_NOTICE } from '#/lib/demo/demo-notice'

import { Route } from './profile'

const principal: Principal = {
  id: 'u1',
  email: 'demo@heftra.com',
  name: 'Demo',
  role: 'demo',
  isSystemAdmin: false,
  organizationId: 'org1',
  demo: true,
}

const user = {
  id: 'user_1',
  firstName: 'Demo',
  lastName: 'Visitor',
  fullName: 'Demo Visitor',
  username: null,
  hasImage: false,
  imageUrl: '',
  primaryEmailAddressId: 'e1',
  primaryEmailAddress: { emailAddress: 'demo@heftra.com' },
  emailAddresses: [
    {
      id: 'e1',
      emailAddress: 'demo@heftra.com',
      verification: { status: 'verified' },
    },
  ],
  externalAccounts: [],
  passwordEnabled: true,
  update: vi.fn(),
  setProfileImage: vi.fn(),
  updatePassword: vi.fn(),
  createEmailAddress: vi.fn(),
  getSessions: vi.fn(),
}

vi.mock('#/lib/auth/auth', async (importOriginal) => ({
  ...(await importOriginal<typeof AuthModule>()),
  usePrincipal: () => principal,
}))

vi.mock('@clerk/tanstack-react-start', () => ({
  useUser: () => ({ user, isLoaded: true }),
  useSession: () => ({ session: { id: 'sess_current' } }),
}))

vi.mock('#/components/settings/profile/preferences-panel', () => ({
  PreferencesPanel: () => null,
}))

const ProfileSection = Route.options.component as unknown as ComponentType

function renderPage() {
  render(
    <ToastProvider>
      <ProfileSection />
    </ToastProvider>,
  )
}

function renameTo(firstName: string) {
  fireEvent.change(screen.getByLabelText('First name'), {
    target: { value: firstName },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Save changes' }))
}

beforeEach(() => {
  user.update.mockResolvedValue(undefined)
  user.getSessions.mockResolvedValue([])
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('Profile route for the demo login', () => {
  it('offers every profile and security control, like any account', async () => {
    principal.demo = true
    renderPage()

    expect(screen.getByLabelText('First name')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Change photo' })).toBeTruthy()
    expect(screen.getByLabelText('New email address')).toBeTruthy()
    expect(screen.getByLabelText('New password')).toBeTruthy()
    expect(await screen.findByText('Active sessions')).toBeTruthy()
  })

  it('keeps a renamed profile out of Clerk and says why', async () => {
    principal.demo = true
    renderPage()

    renameTo('Someone')

    expect(await screen.findByText(DEMO_NOTICE.title)).toBeTruthy()
    expect(screen.getByText(DEMO_REFUSAL)).toBeTruthy()
    expect(screen.queryByText('Couldn’t save your changes')).toBeNull()
    expect(user.update).not.toHaveBeenCalled()
  })

  it('saves the rename to Clerk for anyone else', async () => {
    principal.demo = false
    renderPage()

    renameTo('Someone')

    await waitFor(() => {
      expect(user.update).toHaveBeenCalledWith({
        firstName: 'Someone',
        lastName: 'Visitor',
      })
    })
    expect(screen.queryByText(DEMO_NOTICE.title)).toBeNull()
  })
})
