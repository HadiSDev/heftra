import type { ComponentType } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

import { Route } from './emission-factors'

const get = vi.fn()

vi.mock('#/lib/auth/auth', () => ({
  usePrincipal: () => ({ isSystemAdmin: false, role: 'admin' }),
  useApi: () => ({ get }),
}))

const EmissionFactorsRoute = Route.options.component as unknown as ComponentType

describe('Emission factors route', () => {
  it('tells anyone but a system admin it is not for them, without asking the API', () => {
    render(<EmissionFactorsRoute />)

    expect(screen.getByText('System admins only')).toBeTruthy()
    expect(get).not.toHaveBeenCalled()
  })
})
