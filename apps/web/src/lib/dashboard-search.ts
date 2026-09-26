import { fromIsoDate, toIsoDate } from './format/format'
import type { PeriodRead, SpendScope } from './api/spend-report-types'

/** The periods the dashboard offers; `custom` reads `from` and `to`. */
export type PeriodPreset = 'month' | 'quarter' | 'ytd' | '12m' | 'custom'

export const PERIOD_PRESETS: ReadonlyArray<{
  value: PeriodPreset
  label: string
}> = [
  { value: 'month', label: 'This month' },
  { value: 'quarter', label: 'This quarter' },
  { value: 'ytd', label: 'Year to date' },
  { value: '12m', label: 'Last 12 months' },
  { value: 'custom', label: 'Custom' },
]

export const DEFAULT_PRESET: PeriodPreset = 'ytd'

export interface DashboardSearch {
  period?: PeriodPreset
  from?: string
  to?: string
  company_id?: string
}

function str(value: unknown): string | undefined {
  return typeof value === 'string' && value !== '' ? value : undefined
}

function preset(value: unknown): PeriodPreset | undefined {
  return PERIOD_PRESETS.find((option) => option.value === value)?.value
}

function isoDate(value: unknown): string | undefined {
  const text = str(value)
  return text !== undefined && fromIsoDate(text) !== undefined
    ? text
    : undefined
}

/** Parse the dashboard's search params; a custom period without a valid range falls back to the default. */
export function validateDashboardSearch(
  search: Record<string, unknown>,
): DashboardSearch {
  const company_id = str(search.company_id)
  const period = preset(search.period)
  if (period !== 'custom') {
    return { period, company_id }
  }
  const from = isoDate(search.from)
  const to = isoDate(search.to)
  if (from === undefined || to === undefined || from > to) {
    return { company_id }
  }
  return { period, from, to, company_id }
}

function firstOfMonth(day: Date, monthsBack = 0): Date {
  return new Date(day.getFullYear(), day.getMonth() - monthsBack, 1)
}

/** The dates a search covers, resolved against `today`. */
export function resolvePeriod(
  search: DashboardSearch,
  today: Date = new Date(),
): { from: string; to: string } {
  const to = toIsoDate(today) as string
  switch (search.period ?? DEFAULT_PRESET) {
    case 'month':
      return { from: toIsoDate(firstOfMonth(today)) as string, to }
    case 'quarter':
      return {
        from: toIsoDate(
          new Date(
            today.getFullYear(),
            Math.floor(today.getMonth() / 3) * 3,
            1,
          ),
        ) as string,
        to,
      }
    case '12m':
      return { from: toIsoDate(firstOfMonth(today, 11)) as string, to }
    case 'custom':
      return {
        from: search.from ?? to,
        to: search.to ?? to,
      }
    default:
      return {
        from: toIsoDate(new Date(today.getFullYear(), 0, 1)) as string,
        to,
      }
  }
}

/** The report scope for a search: its dates and, when chosen, its company. */
export function spendScope(
  search: DashboardSearch,
  today: Date = new Date(),
): SpendScope {
  return { ...resolvePeriod(search, today), company_id: search.company_id }
}

const dayMonth = new Intl.DateTimeFormat('en-GB', {
  day: 'numeric',
  month: 'short',
})
const dayMonthYear = new Intl.DateTimeFormat('en-GB', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
})

/** A period as a reader says it: "1 Apr – 26 Jun", with the year when it spans two. */
export function describePeriod(period: PeriodRead): string {
  const start = fromIsoDate(period.start)
  const end = fromIsoDate(period.end)
  if (!start || !end) {
    return `${period.start} – ${period.end}`
  }
  const format =
    start.getFullYear() === end.getFullYear() ? dayMonth : dayMonthYear
  return `${format.format(start)} – ${format.format(end)}`
}
