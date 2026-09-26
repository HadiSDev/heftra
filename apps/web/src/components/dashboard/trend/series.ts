import { formatMoney, toNumber } from '#/lib/format/format'
import type { SpendTrendRow, TrendSeries } from '#/lib/api/spend-report-types'

const CATEGORY_COLORS = [
  'var(--color-chart-1)',
  'var(--color-chart-2)',
  'var(--color-chart-3)',
  'var(--color-chart-4)',
  'var(--color-chart-5)',
]

/** How a series is named in the legend and tooltip. */
export function seriesLabel(series: TrendSeries): string {
  if (series.kind === 'other') {
    return 'Other'
  }
  if (series.kind === 'not_categorized') {
    return 'Not categorized'
  }
  return series.name ?? 'Unnamed category'
}

/** The series' colour: one of five for a named category, muted for the rest and the uncategorized. */
export function seriesColor(series: TrendSeries, index: number): string {
  if (series.kind === 'other') {
    return 'var(--color-chart-other)'
  }
  if (series.kind === 'not_categorized') {
    return 'var(--color-chart-uncategorized)'
  }
  return CATEGORY_COLORS[index % CATEGORY_COLORS.length]
}

/** A stable key for a series in the chart's data. */
export function seriesKey(index: number): string {
  return `s${index}`
}

const monthLabel = new Intl.DateTimeFormat('en-GB', { month: 'short' })
const monthYear = new Intl.DateTimeFormat('en-GB', {
  month: 'short',
  year: 'numeric',
})

function monthOf(iso: string): Date {
  return new Date(`${iso}T00:00:00`)
}

/** One chart row per month: its label and each series' spend. */
export function chartRows(
  row: SpendTrendRow,
): Array<Record<string, string | number>> {
  return row.months.map((month, monthIndex) => {
    const entry: Record<string, string | number> = {
      month: monthLabel.format(monthOf(month)),
      monthFull: monthYear.format(monthOf(month)),
    }
    row.series.forEach((series, index) => {
      entry[seriesKey(index)] = toNumber(series.amounts[monthIndex])
    })
    return entry
  })
}

/** Each month's total, read out for assistive technology. */
export function trendSummary(row: SpendTrendRow): string {
  const months = row.months.map((month, monthIndex) => {
    const total = row.series.reduce(
      (sum, series) => sum + toNumber(series.amounts[monthIndex]),
      0,
    )
    return `${monthYear.format(monthOf(month))} ${formatMoney(total, row.currency)}`
  })
  return `Spend by month in ${row.currency}: ${months.join(', ')}.`
}
