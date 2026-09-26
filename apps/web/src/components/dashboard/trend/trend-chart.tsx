import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { TooltipContentProps } from 'recharts'
import { formatMoney } from '#/lib/format/format'
import type { SpendTrendRow } from '#/lib/api/spend-report-types'
import {
  chartRows,
  seriesColor,
  seriesKey,
  seriesLabel,
  trendSummary,
} from './series'

const compact = new Intl.NumberFormat('en-GB', {
  notation: 'compact',
  maximumFractionDigits: 1,
})

function MonthTooltip({
  active,
  payload,
  row,
}: Pick<TooltipContentProps<number, string>, 'active' | 'payload'> & {
  row: SpendTrendRow
}) {
  if (!active || payload.length === 0) {
    return null
  }
  const month = payload[0].payload as Record<string, string | number>
  const parts = row.series
    .map((series, index) => ({
      label: seriesLabel(series),
      color: seriesColor(series, index),
      amount: Number(month[seriesKey(index)] ?? 0),
    }))
    .filter((part) => part.amount !== 0)
  const total = parts.reduce((sum, part) => sum + part.amount, 0)
  return (
    <div className="min-w-44 rounded-lg border border-border bg-popover p-3 text-xs text-popover-foreground shadow-panel">
      <p className="mb-2 font-medium">{month.monthFull}</p>
      <ul className="flex flex-col gap-1">
        {parts.map((part) => (
          <li
            key={part.label}
            className="flex items-center justify-between gap-4"
          >
            <span className="flex items-center gap-1.5">
              <span
                aria-hidden="true"
                className="size-2 rounded-full"
                style={{ background: part.color }}
              />
              {part.label}
            </span>
            <span className="font-mono tabular-nums">
              {formatMoney(part.amount, row.currency)}
            </span>
          </li>
        ))}
      </ul>
      <p className="mt-2 flex justify-between gap-4 border-t border-border pt-2 font-medium">
        <span>Total</span>
        <span className="font-mono tabular-nums">
          {formatMoney(total, row.currency)}
        </span>
      </p>
    </div>
  )
}

/** Twelve months of one currency's spend, stacked by its top categories. */
export function TrendChart({
  row,
  showCurrency,
}: {
  row: SpendTrendRow
  showCurrency: boolean
}) {
  const data = chartRows(row)
  return (
    <figure className="flex min-w-0 flex-col gap-3">
      {showCurrency ? (
        <figcaption className="text-xs font-medium text-muted-foreground">
          {row.currency}
        </figcaption>
      ) : null}
      <p className="sr-only">{trendSummary(row)}</p>
      <div aria-hidden="true" className="h-64 w-full">
        <ResponsiveContainer
          width="100%"
          height="100%"
          initialDimension={{ width: 640, height: 256 }}
        >
          <BarChart
            data={data}
            margin={{ top: 4, right: 4, bottom: 0, left: 0 }}
          >
            <CartesianGrid vertical={false} stroke="var(--color-border)" />
            <XAxis
              dataKey="month"
              tickLine={false}
              axisLine={false}
              tick={{ fill: 'var(--color-muted-foreground)', fontSize: 12 }}
            />
            <YAxis
              width={44}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value: number) => compact.format(value)}
              tick={{ fill: 'var(--color-muted-foreground)', fontSize: 12 }}
            />
            <Tooltip
              cursor={{ fill: 'var(--color-muted)', opacity: 0.5 }}
              content={(props) => <MonthTooltip {...props} row={row} />}
            />
            {row.series.map((series, index) => (
              <Bar
                key={seriesKey(index)}
                dataKey={seriesKey(index)}
                stackId="spend"
                fill={seriesColor(series, index)}
                isAnimationActive={false}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
      <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
        {row.series.map((series, index) => (
          <li
            key={seriesKey(index)}
            className="inline-flex items-center gap-1.5"
          >
            <span
              aria-hidden="true"
              className="size-2.5 rounded-sm"
              style={{ background: seriesColor(series, index) }}
            />
            {seriesLabel(series)}
          </li>
        ))}
      </ul>
    </figure>
  )
}
