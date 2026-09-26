import type { ReactNode } from 'react'
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest'
import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from '@testing-library/react'
import type * as RouterModule from '@tanstack/react-router'
import type {
  SpendBreakdown,
  SpendInsights,
  SpendOverview,
  SpendTrend,
} from '#/lib/api/spend-report-types'
import { DashboardView } from './dashboard-view'
import type { DashboardViewProps } from './dashboard-view'

vi.mock('@tanstack/react-router', async (importOriginal) => {
  const actual = await importOriginal<typeof RouterModule>()
  return {
    ...actual,
    Link: ({
      to,
      params,
      search,
      children,
      ...props
    }: {
      to: string
      params?: Record<string, string>
      search?: Record<string, unknown>
      children: ReactNode
    }) => {
      const path = Object.entries(params ?? {}).reduce(
        (href, [key, value]) => href.replace(`$${key}`, value),
        to,
      )
      const query = new URLSearchParams(
        Object.entries(search ?? {}).map(([key, value]) => [
          key,
          String(value),
        ]),
      ).toString()
      return (
        <a href={query ? `${path}?${query}` : path} {...props}>
          {children}
        </a>
      )
    },
  }
})

class NoResize {
  observe() {}
  unobserve() {}
  disconnect() {}
}

beforeAll(() => {
  vi.stubGlobal('ResizeObserver', NoResize)
})

afterEach(() => {
  cleanup()
})

const PERIODS = {
  period: { start: '2026-07-01', end: '2026-09-26' },
  comparison: { start: '2026-04-01', end: '2026-06-26' },
}

function overview(overrides: Partial<SpendOverview> = {}): SpendOverview {
  return {
    ...PERIODS,
    rows: [
      {
        currency: 'DKK',
        spend: '12000',
        comparison_spend: '10000',
        categorized_spend: '9000',
        unconverted_vouchers: 0,
        months: Array.from({ length: 12 }, (_, index) => ({
          month: `2026-${String((index % 12) + 1).padStart(2, '0')}-01`,
          amount: '1000',
        })),
        active_suppliers: 14,
        new_suppliers: 2,
      },
    ],
    attention: {
      needs_review_lines: 3,
      failed_documents: 1,
      totals_mismatch: 0,
    },
    ...overrides,
  }
}

const TREND: SpendTrend = {
  ...PERIODS,
  rows: [
    {
      currency: 'DKK',
      months: ['2026-08-01', '2026-09-01'],
      series: [
        { kind: 'category', name: 'Technology', amounts: ['700', '800'] },
        { kind: 'not_categorized', name: null, amounts: ['100', '0'] },
      ],
    },
  ],
}

const BREAKDOWN: SpendBreakdown = {
  ...PERIODS,
  rows: [
    {
      currency: 'DKK',
      spend: '12000',
      categories: [
        {
          name: 'Technology',
          spend: '9000',
          comparison_spend: '6000',
          children: [
            {
              name: 'Software',
              spend: '6000',
              comparison_spend: '4000',
              children: [],
            },
            {
              name: 'Hardware',
              spend: '3000',
              comparison_spend: '2000',
              children: [],
            },
          ],
        },
        { name: null, spend: '3000', comparison_spend: '0', children: [] },
      ],
      suppliers: [
        {
          id: 'v1',
          name: 'Hetzner Online GmbH',
          country_code: 'DE',
          spend: '4000',
          comparison_spend: '4000',
        },
      ],
    },
  ],
}

const INSIGHTS: SpendInsights = {
  ...PERIODS,
  rows: [
    {
      currency: 'DKK',
      new_suppliers: [
        {
          id: 'v9',
          name: 'Fresh ApS',
          amount: '500',
          comparison_amount: null,
          active_months: null,
        },
      ],
      increases: [],
      recurring: [
        {
          id: 'v2',
          name: 'Figma Inc',
          amount: '400',
          comparison_amount: null,
          active_months: 4,
        },
      ],
      uncategorized: [
        {
          voucher_id: '4821',
          entry_id: null,
          invoice_id: 'i1',
          supplier_id: 'v3',
          supplier_name: 'Shop ApS',
          spent_on: '2026-08-03',
          amount: '250',
        },
      ],
    },
  ],
}

function setup(overrides: Partial<DashboardViewProps> = {}) {
  const props: DashboardViewProps = {
    search: { period: 'quarter' },
    resolved: { from: '2026-07-01', to: '2026-09-26' },
    companies: [],
    overview: { data: overview(), error: false },
    trend: { data: TREND, error: false },
    breakdown: { data: BREAKDOWN, error: false },
    insights: { data: INSIGHTS, error: false },
    onSearchChange: vi.fn(),
    ...overrides,
  }
  render(<DashboardView {...props} />)
  return props
}

function tile(name: string): HTMLElement {
  return screen.getByRole('region', { name })
}

describe('DashboardView — tiles', () => {
  it('shows the spend with its change against the named comparison period', () => {
    setup()

    const spend = within(tile('Spend'))
    expect(spend.getByText(/DKK\s12,000\.00/)).toBeTruthy()
    expect(spend.getByText('+20%')).toBeTruthy()
    expect(spend.getByText(/vs 1 Apr – 26 Jun/)).toBeTruthy()
  })

  it('shows how much of the spend is categorized', () => {
    setup()

    expect(within(tile('Categorized')).getByText('75%')).toBeTruthy()
  })

  it('links each thing needing attention to the vouchers it counts', () => {
    setup()

    const attention = within(tile('Needs attention'))
    expect(
      attention
        .getByRole('link', { name: /3 lines to review/ })
        .getAttribute('href'),
    ).toBe('/invoice-lines?needs_review=true')
    expect(
      attention
        .getByRole('link', { name: /1 document failed/ })
        .getAttribute('href'),
    ).toBe('/invoice-lines?document=failed')
    expect(attention.queryByText(/disagree/)).toBeNull()
  })

  it('says all is clear when nothing needs attention', () => {
    setup({
      overview: {
        data: overview({
          attention: {
            needs_review_lines: 0,
            failed_documents: 0,
            totals_mismatch: 0,
          },
        }),
        error: false,
      },
    })

    expect(within(tile('Needs attention')).getByText('All clear')).toBeTruthy()
  })

  it('counts the suppliers and the new ones', () => {
    setup()

    const suppliers = within(tile('Suppliers'))
    expect(suppliers.getByText('14')).toBeTruthy()
    expect(suppliers.getByText('2 new in the period')).toBeTruthy()
  })

  it('calls spend with nothing before it new', () => {
    const data = overview()
    data.rows[0].comparison_spend = '0'
    setup({ overview: { data, error: false } })

    expect(within(tile('Spend')).getByText('New')).toBeTruthy()
  })
})

describe('DashboardView — trend', () => {
  it('reads each month out and lists the categories', () => {
    setup()

    const trend = within(
      screen.getByRole('region', { name: 'Spend over time' }),
    )
    expect(
      trend.getByText(/Spend by month in DKK: Aug 2026 DKK\s800\.00/),
    ).toBeTruthy()
    expect(trend.getByText('Technology')).toBeTruthy()
    expect(trend.getByText('Not categorized')).toBeTruthy()
  })
})

describe('DashboardView — breakdowns', () => {
  it('shows categories largest first with the uncategorized last, and opens one to its children', () => {
    setup()

    const categories = within(
      screen.getByRole('region', { name: 'Spend by category in DKK' }),
    )
    expect(categories.getByText('Not categorized')).toBeTruthy()
    expect(categories.queryByText('Software')).toBeNull()

    fireEvent.click(categories.getByRole('button', { name: /Technology/ }))

    expect(categories.getByText('Software')).toBeTruthy()
    expect(categories.getByText('Hardware')).toBeTruthy()
    expect(categories.getByText('75%')).toBeTruthy()
  })

  it('opens a top supplier’s page', () => {
    setup()

    const link = screen.getByRole('link', { name: 'Hetzner Online GmbH' })
    expect(link.getAttribute('href')).toBe('/suppliers/v1')
  })
})

describe('DashboardView — insights', () => {
  it('lists the insights there are and leaves out the empty headings', () => {
    setup()

    const insights = within(screen.getByRole('region', { name: 'Insights' }))
    expect(insights.getByRole('region', { name: 'New suppliers' })).toBeTruthy()
    expect(
      insights.getByRole('region', { name: 'Recurring spend' }),
    ).toBeTruthy()
    expect(
      insights.queryByRole('region', { name: 'Biggest increases' }),
    ).toBeNull()
  })

  it('opens an uncategorized voucher in Spend Lines', () => {
    setup()

    expect(
      screen.getByRole('link', { name: /Shop ApS/ }).getAttribute('href'),
    ).toBe('/invoice-lines?voucher=4821')
  })
})

describe('DashboardView — states', () => {
  it('holds each section’s place while it loads', () => {
    setup({
      overview: { data: undefined, error: false },
      trend: { data: undefined, error: false },
      breakdown: { data: undefined, error: false },
      insights: { data: undefined, error: false },
    })

    expect(screen.getByTestId('tiles-loading')).toBeTruthy()
    expect(screen.getByTestId('Spend over time-loading')).toBeTruthy()
    expect(screen.getByTestId('Insights-loading')).toBeTruthy()
  })

  it('says when the period had no spend and offers the last 12 months', () => {
    const props = setup({
      overview: { data: overview({ rows: [] }), error: false },
    })

    expect(screen.getByText('No spend in this period')).toBeTruthy()
    fireEvent.click(
      screen.getByRole('button', { name: 'Show the last 12 months' }),
    )
    expect(props.onSearchChange).toHaveBeenCalledWith(
      expect.objectContaining({ period: '12m' }),
    )
  })

  it('shows a failed section’s error without hiding the others', () => {
    setup({ insights: { data: undefined, error: true } })

    const insights = within(screen.getByRole('region', { name: 'Insights' }))
    expect(insights.getByRole('alert')).toBeTruthy()
    expect(tile('Spend')).toBeTruthy()
    expect(screen.getByRole('region', { name: 'Spend over time' })).toBeTruthy()
  })
})
