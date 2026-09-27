import type * as React from 'react'
import { Button, Card, Progress, Skeleton } from '#/components/ui'
import { formatEmissions } from '#/lib/format/emissions'
import { formatCount, toNumber } from '#/lib/format/format'
import type {
  EmissionsSpendRow,
  EmissionsSummaryRead,
  FactorSetRead,
} from '#/lib/api/emission-types'
import { Metric } from '../summary/metric'
import { formatShare } from '../summary/spend-coverage'
import { EmissionsMethod } from './emissions-method'
import { EMISSIONS_STATUS_REASON, NOT_ESTIMATED } from './status-labels'

const CARD_CLASS =
  'grid divide-y divide-border p-0 md:grid-cols-3 md:divide-x md:divide-y-0'

function estimatedShare(row: EmissionsSpendRow): number | null {
  const posted = toNumber(row.posted_spend)
  if (posted <= 0) {
    return null
  }
  return toNumber(row.estimated_spend) / posted
}

function SpendEstimated({ rows }: { rows: Array<EmissionsSpendRow> }) {
  if (rows.length === 1) {
    const share = estimatedShare(rows[0])
    if (share === null) {
      return <>No posted spend to compare with</>
    }
    return (
      <div className="flex flex-col gap-2">
        <span>of posted spend has an estimate</span>
        <Progress
          aria-label="Share of posted spend estimated"
          value={Math.min(100, Math.round(share * 100))}
        />
      </div>
    )
  }
  return (
    <ul className="flex flex-col gap-0.5">
      {rows.map((row) => {
        const share = estimatedShare(row)
        return (
          <li key={row.currency}>
            {row.currency}: {share === null ? '—' : formatShare(share)}
          </li>
        )
      })}
    </ul>
  )
}

function shareValue(rows: Array<EmissionsSpendRow>): string {
  if (rows.length !== 1) {
    return `${rows.length} currencies`
  }
  const share = estimatedShare(rows[0])
  return share === null ? '—' : formatShare(share)
}

function NotEstimated({ summary }: { summary: EmissionsSummaryRead }) {
  const reasons = NOT_ESTIMATED.map((status) => ({
    status,
    count: summary.vouchers_by_status[status] ?? 0,
  })).filter((reason) => reason.count > 0)
  const partial = summary.vouchers_by_status.partial ?? 0
  if (reasons.length === 0 && partial === 0) {
    return <>Every voucher has an estimate</>
  }
  return (
    <ul className="flex flex-col gap-0.5">
      {reasons.map(({ status, count }) => (
        <li key={status}>
          {formatCount(count)}: {EMISSIONS_STATUS_REASON[status].toLowerCase()}
        </li>
      ))}
      {partial > 0 ? (
        <li>{formatCount(partial)} estimated from only some of their lines</li>
      ) : null}
    </ul>
  )
}

function EmissionsFigures({
  summary,
  factorSet,
}: {
  summary: EmissionsSummaryRead
  factorSet: FactorSetRead
}) {
  const notEstimated = NOT_ESTIMATED.reduce(
    (sum, status) => sum + (summary.vouchers_by_status[status] ?? 0),
    0,
  )
  return (
    <Card aria-label="Estimated emissions" className={CARD_CLASS}>
      <Metric
        caption="Estimated emissions"
        value={formatEmissions(summary.kg_co2e ?? 0)}
      >
        <div className="flex flex-col gap-0.5">
          <EmissionsMethod factorSet={factorSet} />
          <span className="text-xs">{factorSet.attribution}</span>
        </div>
      </Metric>
      <Metric caption="Spend estimated" value={shareValue(summary.spend)}>
        <SpendEstimated rows={summary.spend} />
      </Metric>
      <Metric
        caption="Vouchers not estimated"
        value={formatCount(notEstimated)}
      >
        <NotEstimated summary={summary} />
      </Metric>
    </Card>
  )
}

function Notice({
  title,
  children,
}: {
  title: string
  children?: React.ReactNode
}) {
  return (
    <Card
      aria-label="Estimated emissions"
      className="flex min-h-28 flex-wrap items-center justify-between gap-3 px-5 py-4"
    >
      <div>
        <h3 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
          Estimated emissions
        </h3>
        <p className="mt-1 text-sm text-foreground">{title}</p>
      </div>
      {children}
    </Card>
  )
}

function EmissionsSkeleton() {
  return (
    <Card data-testid="emissions-loading" className={CARD_CLASS}>
      {[0, 1, 2].map((index) => (
        <div key={index} className="flex flex-col gap-2 px-5 py-4">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-7 w-36" />
          <Skeleton className="h-4 w-full" />
        </div>
      ))}
    </Card>
  )
}

export interface EmissionsCardProps {
  /** Undefined until first loaded. */
  summary: EmissionsSummaryRead | undefined
  error: boolean
  onRetry: () => void
}

/** The listed vouchers' estimated emissions, how much spend they cover, and what is missing. */
export function EmissionsCard({ summary, error, onRetry }: EmissionsCardProps) {
  if (error) {
    return (
      <Notice title="Couldn’t load the emissions estimate.">
        <Button size="sm" variant="outline" onClick={onRetry}>
          Try again
        </Button>
      </Notice>
    )
  }
  if (summary === undefined) {
    return <EmissionsSkeleton />
  }
  if (summary.factor_set === null) {
    return (
      <Notice title="No emission factors are imported, so no emissions are estimated yet." />
    )
  }
  return <EmissionsFigures summary={summary} factorSet={summary.factor_set} />
}
