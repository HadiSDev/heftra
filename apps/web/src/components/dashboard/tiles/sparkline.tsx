import { Area, AreaChart, ResponsiveContainer } from 'recharts'
import { toNumber } from '#/lib/format/format'
import type { MonthSpend } from '#/lib/api/spend-report-types'

/** Twelve months of spend as a small line, for shape rather than reading. */
export function Sparkline({ months }: { months: Array<MonthSpend> }) {
  const data = months.map((month) => ({ amount: toNumber(month.amount) }))
  return (
    <div aria-hidden="true" className="h-8 w-full">
      <ResponsiveContainer
        width="100%"
        height="100%"
        initialDimension={{ width: 160, height: 32 }}
      >
        <AreaChart
          data={data}
          margin={{ top: 2, right: 0, bottom: 0, left: 0 }}
        >
          <Area
            type="monotone"
            dataKey="amount"
            stroke="var(--color-chart-1)"
            strokeWidth={1.5}
            fill="var(--color-chart-1)"
            fillOpacity={0.12}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
