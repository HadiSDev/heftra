import { Link } from '@tanstack/react-router'
import { Building2 } from 'lucide-react'
import { formatCount } from '#/lib/format/format'
import type { SpendOverviewRow } from '#/lib/api/spend-report-types'
import { CurrencyCaption, Tile } from './tile'

/** How many suppliers had spend in the period, and how many of them are new. */
export function SuppliersTile({ rows }: { rows: Array<SpendOverviewRow> }) {
  return (
    <Tile caption="Suppliers" icon={<Building2 />}>
      {rows.map((row) => (
        <div key={row.currency} className="flex min-w-0 flex-col gap-1">
          <CurrencyCaption currency={row.currency} shown={rows.length > 1} />
          <span className="font-display text-2xl font-semibold tracking-tight tabular-nums">
            {formatCount(row.active_suppliers)}
          </span>
          <span className="text-xs text-muted-foreground">
            {row.new_suppliers > 0
              ? `${formatCount(row.new_suppliers)} new in the period`
              : 'None new in the period'}
          </span>
        </div>
      ))}
      <Link
        to="/suppliers"
        className="text-xs font-medium text-primary hover:underline"
      >
        Open Suppliers
      </Link>
    </Tile>
  )
}
