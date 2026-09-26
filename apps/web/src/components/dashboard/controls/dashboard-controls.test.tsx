import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import type { CompanyRead } from '#/lib/api/types'
import { DashboardControls } from './dashboard-controls'
import type { DashboardControlsProps } from './dashboard-controls'

afterEach(() => {
  cleanup()
})

function company(id: string, name: string): CompanyRead {
  return {
    id,
    name,
    country_code: 'DK',
    vat_number: null,
    base_currency: 'DKK',
    is_active: true,
    deactivated_at: null,
    spend_tree_id: null,
    spend_tree_name: null,
  }
}

function setup(overrides: Partial<DashboardControlsProps> = {}) {
  const props: DashboardControlsProps = {
    search: {},
    resolved: { from: '2026-01-01', to: '2026-09-26' },
    companies: [company('c1', 'Acme A/S')],
    onChange: vi.fn(),
    ...overrides,
  }
  render(<DashboardControls {...props} />)
  return props
}

describe('DashboardControls', () => {
  it('offers the period, defaulting to year to date', () => {
    setup()

    expect(
      screen.getByRole('combobox', { name: 'Period' }).textContent,
    ).toContain('Year to date')
  })

  it('asks for dates only for a custom range', () => {
    setup()
    expect(screen.queryByRole('button', { name: 'From' })).toBeNull()
    cleanup()

    setup({
      search: { period: 'custom', from: '2026-07-10', to: '2026-07-19' },
      resolved: { from: '2026-07-10', to: '2026-07-19' },
    })
    expect(screen.getByRole('button', { name: 'From' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'To' })).toBeTruthy()
  })

  it('offers a company only when there is more than one', () => {
    setup()
    expect(screen.queryByRole('combobox', { name: 'Company' })).toBeNull()
    cleanup()

    setup({ companies: [company('c1', 'Acme A/S'), company('c2', 'Acme AB')] })
    expect(screen.getByRole('combobox', { name: 'Company' })).toBeTruthy()
  })
})
