import {
  DatePicker,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '#/components/ui'
import { fromIsoDate, toIsoDate } from '#/lib/format/format'
import { DEFAULT_PRESET, PERIOD_PRESETS } from '#/lib/dashboard-search'
import type { DashboardSearch, PeriodPreset } from '#/lib/dashboard-search'
import type { CompanyRead } from '#/lib/api/types'

const ALL = '__all__'
const CONTROL = 'h-9 w-full sm:w-44'

export interface DashboardControlsProps {
  search: DashboardSearch
  /** The dates the search resolves to, used to start a custom range from them. */
  resolved: { from: string; to: string }
  companies: Array<CompanyRead>
  onChange: (next: DashboardSearch) => void
}

/** The period and the company the dashboard is read for. */
export function DashboardControls({
  search,
  resolved,
  companies,
  onChange,
}: DashboardControlsProps) {
  const period = search.period ?? DEFAULT_PRESET

  function choosePeriod(next: PeriodPreset) {
    if (next === 'custom') {
      onChange({
        ...search,
        period: next,
        from: resolved.from,
        to: resolved.to,
      })
      return
    }
    onChange({ ...search, period: next, from: undefined, to: undefined })
  }

  function chooseDate(field: 'from' | 'to', date: Date | undefined) {
    const value = toIsoDate(date)
    if (value === undefined) {
      return
    }
    const range = { from: resolved.from, to: resolved.to, [field]: value }
    if (range.from > range.to) {
      return
    }
    onChange({ ...search, period: 'custom', ...range })
  }

  return (
    <div className="flex flex-wrap items-end gap-3">
      <label className="flex w-full flex-col gap-1.5 sm:w-auto">
        <span className="text-xs font-medium text-muted-foreground">
          Period
        </span>
        <Select
          value={period}
          onValueChange={(next: string | null) => {
            const preset = PERIOD_PRESETS.find(
              (option) => option.value === next,
            )
            if (preset) {
              choosePeriod(preset.value)
            }
          }}
        >
          <SelectTrigger className={CONTROL} aria-label="Period">
            <SelectValue items={PERIOD_PRESETS} />
          </SelectTrigger>
          <SelectContent>
            {PERIOD_PRESETS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </label>

      {period === 'custom' ? (
        <>
          <label className="flex w-full flex-col gap-1.5 sm:w-auto">
            <span className="text-xs font-medium text-muted-foreground">
              From
            </span>
            <DatePicker
              className={CONTROL}
              aria-label="From"
              value={fromIsoDate(resolved.from)}
              onChange={(date) => chooseDate('from', date)}
            />
          </label>
          <label className="flex w-full flex-col gap-1.5 sm:w-auto">
            <span className="text-xs font-medium text-muted-foreground">
              To
            </span>
            <DatePicker
              className={CONTROL}
              aria-label="To"
              value={fromIsoDate(resolved.to)}
              onChange={(date) => chooseDate('to', date)}
            />
          </label>
        </>
      ) : null}

      {companies.length > 1 ? (
        <label className="flex w-full flex-col gap-1.5 sm:w-auto">
          <span className="text-xs font-medium text-muted-foreground">
            Company
          </span>
          <Select
            value={search.company_id ?? ''}
            onValueChange={(next: string | null) =>
              onChange({
                ...search,
                company_id: next && next !== ALL ? next : undefined,
              })
            }
          >
            <SelectTrigger className={CONTROL} aria-label="Company">
              <SelectValue
                placeholder="All companies"
                items={companies.map((company) => ({
                  value: company.id,
                  label: company.name,
                }))}
              />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>All companies</SelectItem>
              {companies.map((company) => (
                <SelectItem key={company.id} value={company.id}>
                  {company.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </label>
      ) : null}
    </div>
  )
}
