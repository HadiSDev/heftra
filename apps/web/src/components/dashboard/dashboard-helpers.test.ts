import { describe, expect, it } from 'vitest'
import { changeOf, describeChange, formatShare } from './change'
import {
  chartRows,
  seriesColor,
  seriesLabel,
  trendSummary,
} from './trend/series'
import type { SpendTrendRow } from '#/lib/api/spend-report-types'

describe('changeOf', () => {
  it('measures a rise and a fall against the comparison', () => {
    expect(describeChange(changeOf('12000', '10000'))).toBe('+20%')
    expect(describeChange(changeOf('8000', '10000'))).toBe('−20%')
  })

  it('calls spend with nothing before it new, and shows nothing when neither had any', () => {
    expect(changeOf('50', '0')).toEqual({ kind: 'new' })
    expect(changeOf('0', '0')).toEqual({ kind: 'none' })
    expect(describeChange(changeOf('0', '0'))).toBe('')
  })

  it('treats a hair of change as none', () => {
    expect(describeChange(changeOf('1000.01', '1000'))).toBe('0%')
  })
})

describe('formatShare', () => {
  it('shows a sliver as less than one percent', () => {
    expect(formatShare(0.004)).toBe('<1%')
    expect(formatShare(0.75)).toBe('75%')
  })
})

const ROW: SpendTrendRow = {
  currency: 'DKK',
  months: ['2026-08-01', '2026-09-01'],
  series: [
    { kind: 'category', name: 'Technology', amounts: ['100', '200'] },
    { kind: 'other', name: null, amounts: ['10', '0'] },
    { kind: 'not_categorized', name: null, amounts: ['5', '5'] },
  ],
}

describe('trend series', () => {
  it('names and colours each kind of series', () => {
    expect(ROW.series.map(seriesLabel)).toEqual([
      'Technology',
      'Other',
      'Not categorized',
    ])
    expect(seriesColor(ROW.series[0], 0)).toBe('var(--color-chart-1)')
    expect(seriesColor(ROW.series[1], 1)).toBe('var(--color-chart-other)')
  })

  it('makes one chart row per month', () => {
    expect(chartRows(ROW)).toEqual([
      { month: 'Aug', monthFull: 'Aug 2026', s0: 100, s1: 10, s2: 5 },
      { month: 'Sept', monthFull: 'Sept 2026', s0: 200, s1: 0, s2: 5 },
    ])
  })

  it('reads each month out in words', () => {
    expect(trendSummary(ROW)).toMatch(
      /^Spend by month in DKK: Aug 2026 DKK\s115\.00, Sept 2026 DKK\s205\.00\.$/,
    )
  })
})
