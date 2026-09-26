import { Skeleton } from '#/components/ui'
import type { SpendOverview } from '#/lib/api/spend-report-types'
import { AttentionTile } from './attention-tile'
import { CategorizedTile } from './categorized-tile'
import { SpendTile } from './spend-tile'
import { SuppliersTile } from './suppliers-tile'

const GRID = 'grid gap-4 sm:grid-cols-2 xl:grid-cols-4'

/** The four tiles, or their placeholders at the same size. */
export function OverviewTiles({
  overview,
  error,
}: {
  overview: SpendOverview | undefined
  error: boolean
}) {
  if (error) {
    return (
      <p
        role="alert"
        className="rounded-card border border-border p-5 text-sm text-muted-foreground"
      >
        Couldn’t load the dashboard’s figures. Reload to try again.
      </p>
    )
  }
  if (overview === undefined) {
    return (
      <div data-testid="tiles-loading" className={GRID}>
        {[0, 1, 2, 3].map((index) => (
          <Skeleton key={index} className="h-44 rounded-card" />
        ))}
      </div>
    )
  }
  return (
    <div className={GRID}>
      <SpendTile rows={overview.rows} comparison={overview.comparison} />
      <CategorizedTile rows={overview.rows} />
      <AttentionTile attention={overview.attention} />
      <SuppliersTile rows={overview.rows} />
    </div>
  )
}
