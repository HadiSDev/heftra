import type { ComponentType, ReactNode } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import type * as RouterModule from '@tanstack/react-router'

import { Route } from './settings'

const principal = { isSystemAdmin: false }

vi.mock('#/lib/auth/auth', () => ({
  usePrincipal: () => principal,
}))

vi.mock('@tanstack/react-router', async (importOriginal) => {
  const actual = await importOriginal<typeof RouterModule>()
  return {
    ...actual,
    Outlet: () => null,
    useRouterState: () => '/settings/profile',
    Link: ({
      to,
      children,
      ...props
    }: {
      to: string
      children?: ReactNode
    }) => (
      <a href={to} {...props}>
        {children}
      </a>
    ),
  }
})

const SettingsLayout = Route.options.component as unknown as ComponentType

afterEach(() => {
  cleanup()
})

describe('Settings tabs', () => {
  it('offers Emission factors to a system admin, last', () => {
    principal.isSystemAdmin = true
    render(<SettingsLayout />)

    const tabs = screen.getAllByRole('tab').map((tab) => tab.textContent)
    expect(tabs.at(-1)).toBe('Emission factors')
  })

  it('hides it from everyone else', () => {
    principal.isSystemAdmin = false
    render(<SettingsLayout />)

    expect(screen.queryByRole('tab', { name: 'Emission factors' })).toBeNull()
  })
})
