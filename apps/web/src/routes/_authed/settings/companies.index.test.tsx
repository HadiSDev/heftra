import type { ComponentType } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ToastProvider } from '#/components/ui'
import type * as RouterModule from '@tanstack/react-router'
import type * as AuthModule from '#/lib/auth/auth'
import type { Principal } from '#/lib/auth/auth'
import type { CompanyRead } from '#/lib/api/types'

import { Route } from './companies.index'

const DEMO: Principal = {
  id: 'u1',
  email: 'demo@heftra.com',
  name: 'Demo',
  role: 'demo',
  isSystemAdmin: false,
  organizationId: 'org1',
  demo: true,
}

const ACME: CompanyRead = {
  id: 'c1',
  name: 'Acme A/S',
  country_code: 'DK',
  vat_number: 'DK12345678',
  base_currency: 'DKK',
  is_active: true,
  deactivated_at: null,
  spend_tree_id: 'tree1',
  spend_tree_name: 'Default spend tree',
  website: null,
  description: null,
  description_source: null,
}

const get = vi.fn()

vi.mock('#/lib/auth/auth', async (importOriginal) => ({
  ...(await importOriginal<typeof AuthModule>()),
  usePrincipal: () => DEMO,
  useApi: () => ({ get }),
}))

vi.mock('@tanstack/react-router', async (importOriginal) => ({
  ...(await importOriginal<typeof RouterModule>()),
  useNavigate: () => vi.fn(),
}))

const CompaniesSection = Route.options.component as unknown as ComponentType

beforeEach(() => {
  get.mockImplementation((path: string) =>
    Promise.resolve(path === '/api/v1/companies' ? [ACME] : []),
  )
})

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('Companies route for the demo login', () => {
  it('offers adding and editing companies, like an admin', async () => {
    render(
      <QueryClientProvider client={new QueryClient()}>
        <ToastProvider>
          <CompaniesSection />
        </ToastProvider>
      </QueryClientProvider>,
    )

    expect(await screen.findByText('Acme A/S')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Add company' })).toBeTruthy()
    expect(
      screen.queryByRole('button', { name: 'Run pipeline for Acme A/S' }),
    ).toBeNull()

    fireEvent.click(
      screen.getByRole('button', { name: 'Actions for Acme A/S' }),
    )
    const items = (await screen.findAllByRole('menuitem')).map(
      (item) => item.textContent,
    )
    expect(items).toContain('Edit')
    expect(items).toContain('Deactivate')
    expect(items).not.toContain('Delete')
  })
})
