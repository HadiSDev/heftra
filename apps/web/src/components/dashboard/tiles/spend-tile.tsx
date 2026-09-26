import { Wallet } from 'lucide-react'
import { formatCount, formatMoney } from '#/lib/format/format'
import { describePeriod } from '#/lib/dashboard-search'
import type { PeriodRead, SpendOverviewRow } from '#/lib/api/spend-report-types'
import { ChangeBadge } from '../change-badge'
import { Sparkline } from './sparkline'
import { CurrencyCaption, Tile } from './tile'

/** The period's spend, its change from the comparison period, and twelve months' shape. */
export function SpendTile({
  rows,
  comparison,
}: {
  rows: Array<SpendOverviewRow>
  comparison: PeriodRead
}) {
  return (
    <Tile caption="Spend" icon={<Wallet />}>
      {rows.map((row) => (
        <div key={row.currency} className="flex min-w-0 flex-col gap-1">
          <CurrencyCaption currency={row.currency} shown={rows.length > 1} />
          <div className="flex flex-wrap items-baseline gap-x-2">
            <span className="font-display text-2xl font-semibold tracking-tight tabular-nums">
              {formatMoney(row.spend, row.currency)}
            </span>
            <ChangeBadge now={row.spend} before={row.comparison_spend} />
          </div>
          <span className="text-xs text-muted-foreground">
            vs {describePeriod(comparison)}
            {row.unconverted_vouchers > 0
              ? ` · ${formatCount(row.unconverted_vouchers)} not converted`
              : ''}
          </span>
          <Sparkline months={row.months} />
        </div>
      ))}
    </Tile>
  )
}
