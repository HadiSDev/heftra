import type { ComponentType } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type * as RouterModule from '@tanstack/react-router'
import type * as AuthModule from '#/lib/auth/auth'
import type { Principal } from '#/lib/auth/auth'

import { Route } from './index'

const principal: Principal = {
  id: 'u1',
  email: 'demo@heftra.com',
  name: 'Demo',
  role: 'moderator',
  isSystemAdmin: false,
  organizationId: 'org1',
  demo: false,
}

const get = vi.fn()

vi.mock('#/lib/auth/auth', async (importOriginal) => ({
  ...(await importOriginal<typeof AuthModule>()),
  usePrincipal: () => principal,
  useApi: () => ({ get }),
}))

vi.mock('@tanstack/react-router', async (importOriginal) => ({
  ...(await importOriginal<typeof RouterModule>()),
  useNavigate: () => vi.fn(),
}))

const AgreementsPage = Route.options.component as unknown as ComponentType

function renderPage() {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <AgreementsPage />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.spyOn(Route, 'useSearch').mockReturnValue({})
  get.mockResolvedValue([])
})

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('Agreements route', () => {
  it('offers a manager the upload', async () => {
    principal.demo = false
    principal.role = 'moderator'
    renderPage()

    expect(
      await screen.findByRole('region', { name: 'Upload an agreement' }),
    ).toBeTruthy()
  })

  it('offers the demo login the upload too', async () => {
    principal.demo = true
    principal.role = 'demo'
    renderPage()

    expect(
      await screen.findByRole('region', { name: 'Upload an agreement' }),
    ).toBeTruthy()
  })
})
