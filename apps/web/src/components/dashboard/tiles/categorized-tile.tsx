import { Link } from '@tanstack/react-router'
import { Tags } from 'lucide-react'
import { Progress } from '#/components/ui'
import { formatMoney, toNumber } from '#/lib/format/format'
import type { SpendOverviewRow } from '#/lib/api/spend-report-types'
import { formatShare } from '../change'
import { CurrencyCaption, Tile } from './tile'

/** The share of the period's spend that has a category. */
export function CategorizedTile({ rows }: { rows: Array<SpendOverviewRow> }) {
  return (
    <Tile caption="Categorized" icon={<Tags />}>
      {rows.map((row) => {
        const spend = toNumber(row.spend)
        const share = spend > 0 ? toNumber(row.categorized_spend) / spend : 0
        return (
          <div key={row.currency} className="flex min-w-0 flex-col gap-1.5">
            <CurrencyCaption currency={row.currency} shown={rows.length > 1} />
            <span className="font-display text-2xl font-semibold tracking-tight tabular-nums">
              {formatShare(share)}
            </span>
            <Progress
              aria-label={`Share of spend categorized in ${row.currency}`}
              value={Math.min(100, Math.round(share * 100))}
            />
            <span className="text-xs text-muted-foreground">
              {formatMoney(row.categorized_spend, row.currency)} of{' '}
              {formatMoney(row.spend, row.currency)}
            </span>
          </div>
        )
      })}
      <Link
        to="/invoice-lines"
        className="text-xs font-medium text-primary hover:underline"
      >
        Open Spend Lines
      </Link>
    </Tile>
  )
}
