import { describe, expect, it } from 'vitest'
import {
  describePeriod,
  resolvePeriod,
  spendScope,
  validateDashboardSearch,
} from './dashboard-search'

const TODAY = new Date(2026, 8, 26)

describe('validateDashboardSearch', () => {
  it('reads a preset and a company', () => {
    expect(
      validateDashboardSearch({ period: 'quarter', company_id: 'c1' }),
    ).toEqual({ period: 'quarter', company_id: 'c1' })
  })

  it('ignores a preset it does not know', () => {
    expect(validateDashboardSearch({ period: 'decade' }).period).toBeUndefined()
  })

  it('keeps a custom range only when it is a valid one', () => {
    expect(
      validateDashboardSearch({
        period: 'custom',
        from: '2026-07-10',
        to: '2026-07-19',
      }),
    ).toEqual({ period: 'custom', from: '2026-07-10', to: '2026-07-19' })
    expect(
      validateDashboardSearch({
        period: 'custom',
        from: '2026-07-19',
        to: '2026-07-10',
      }).period,
    ).toBeUndefined()
    expect(
      validateDashboardSearch({ period: 'custom', from: 'soon' }).period,
    ).toBeUndefined()
  })

  it('drops dates that belong to no custom range', () => {
    expect(
      validateDashboardSearch({ period: 'month', from: '2026-01-01' }),
    ).toEqual({ period: 'month' })
  })
})

describe('resolvePeriod', () => {
  it.each([
    ['month', '2026-09-01'],
    ['quarter', '2026-07-01'],
    ['ytd', '2026-01-01'],
    ['12m', '2025-10-01'],
  ] as const)('resolves %s to the days so far', (period, from) => {
    expect(resolvePeriod({ period }, TODAY)).toEqual({ from, to: '2026-09-26' })
  })

  it('defaults to year to date', () => {
    expect(resolvePeriod({}, TODAY)).toEqual({
      from: '2026-01-01',
      to: '2026-09-26',
    })
  })

  it('takes a custom range as it is', () => {
    expect(
      resolvePeriod(
        { period: 'custom', from: '2026-07-10', to: '2026-07-19' },
        TODAY,
      ),
    ).toEqual({ from: '2026-07-10', to: '2026-07-19' })
  })

  it('carries the company into the report scope', () => {
    expect(spendScope({ period: 'month', company_id: 'c1' }, TODAY)).toEqual({
      from: '2026-09-01',
      to: '2026-09-26',
      company_id: 'c1',
    })
  })
})

describe('describePeriod', () => {
  it('names a period within one year without the year', () => {
    expect(describePeriod({ start: '2026-04-01', end: '2026-06-26' })).toBe(
      '1 Apr – 26 Jun',
    )
  })

  it('names a period across years with them', () => {
    expect(describePeriod({ start: '2025-04-01', end: '2026-01-26' })).toBe(
      '1 Apr 2025 – 26 Jan 2026',
    )
  })
})
