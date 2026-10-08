import { RefreshCw } from 'lucide-react'
import {
  Badge,
  Button,
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from '#/components/ui'
import type { AdminPriceIndexRead } from '#/lib/api/admin-emission-factor-types'
import { formatIndexMonth } from '#/lib/format/emissions'
import { formatCount, toNumber } from '#/lib/format/format'

const averageFormat = new Intl.NumberFormat('en-GB', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

export interface PriceIndexCardProps {
  indices: Array<AdminPriceIndexRead>
  refreshing?: boolean
  error?: string | null
  /** Omit to show the indices without a way to refresh them. */
  onRefresh?: (series: string) => void
}

function IndexFigures({ index }: { index: AdminPriceIndexRead }) {
  if (index.months === 0) {
    return (
      <p className="text-sm text-warning">
        Not imported, so estimates are not adjusted for inflation.
      </p>
    )
  }
  return (
    <dl className="grid grid-cols-3 gap-4 text-sm">
      <div>
        <dt className="text-muted-foreground">Latest month</dt>
        <dd className="font-display text-lg font-semibold">
          {index.latest_month ? formatIndexMonth(index.latest_month) : '—'}
        </dd>
      </div>
      <div>
        <dt className="text-muted-foreground">Months</dt>
        <dd className="font-display text-lg font-semibold tabular-nums">
          {formatCount(index.months)}
        </dd>
      </div>
      <div>
        <dt className="text-muted-foreground">
          {index.base_year ?? 'Base'} average
        </dt>
        <dd className="font-display text-lg font-semibold tabular-nums">
          {index.base_average === null
            ? 'Incomplete'
            : averageFormat.format(toNumber(index.base_average))}
        </dd>
      </div>
    </dl>
  )
}

/** The price indices spend is deflated with, and a refresh from FRED. */
export function PriceIndexCard({
  indices,
  refreshing = false,
  error = null,
  onRefresh,
}: PriceIndexCardProps) {
  return (
    <Card role="region" aria-label="Price index" className="flex flex-col">
      <CardHeader>
        <CardTitle>Inflation</CardTitle>
        <CardDescription>
          Spend is taken back to the factor set&apos;s price year with this
          index before its factor is applied.
        </CardDescription>
      </CardHeader>
      <div className="flex flex-col gap-5 px-6 pb-6">
        {indices.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No factor set&apos;s currency has a price index.
          </p>
        ) : null}
        {indices.map((index) => (
          <div key={index.series} className="flex flex-col gap-3">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <span className="font-medium">{index.label}</span>
                <Badge variant="outline">{index.series}</Badge>
              </div>
              {onRefresh ? (
                <Button
                  size="sm"
                  variant="outline"
                  disabled={refreshing}
                  onClick={() => {
                    onRefresh(index.series)
                  }}
                >
                  <RefreshCw className={refreshing ? 'animate-spin' : ''} />
                  {refreshing ? 'Refreshing…' : 'Refresh from FRED'}
                </Button>
              ) : null}
            </div>
            <IndexFigures index={index} />
          </div>
        ))}
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
      </div>
    </Card>
  )
}
