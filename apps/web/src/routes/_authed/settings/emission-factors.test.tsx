import type { ComponentType } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { Route } from './emission-factors'

const get = vi.fn()

vi.mock('#/lib/auth/auth', () => ({
  usePrincipal: () => ({ isSystemAdmin: false, role: 'admin' }),
  useApi: () => ({ get }),
}))

const EmissionFactorsRoute = Route.options.component as unknown as ComponentType

describe('Emission factors route', () => {
  it('shows anyone but a system admin a read-only page, without asking for the imports', async () => {
    get.mockResolvedValue({
      sets: [],
      price_indices: [],
      coverage: [],
    })
    render(
      <QueryClientProvider client={new QueryClient()}>
        <EmissionFactorsRoute />
      </QueryClientProvider>,
    )

    expect(
      await screen.findByRole('region', { name: 'Factor sets' }),
    ).toBeTruthy()
    expect(screen.queryByLabelText('Workbook file')).toBeNull()
    expect(screen.queryByRole('region', { name: 'Recent imports' })).toBeNull()
    expect(get).toHaveBeenCalledTimes(1)
    expect(get.mock.calls[0][0]).not.toContain('/imports')
  })
})
