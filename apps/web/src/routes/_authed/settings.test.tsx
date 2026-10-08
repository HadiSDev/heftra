import type { ComponentType, ReactNode } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import type * as RouterModule from '@tanstack/react-router'

import { Route } from './settings'

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
  it('offers Emission factors to everyone, last', () => {
    render(<SettingsLayout />)

    const tabs = screen.getAllByRole('tab').map((tab) => tab.textContent)
    expect(tabs.at(-1)).toBe('Emission factors')
  })
})
