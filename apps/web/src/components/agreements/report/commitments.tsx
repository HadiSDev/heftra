import { Card, Progress } from '#/components/ui'
import type { CommitmentProgress } from '#/lib/api/agreement-types'
import { shareOf } from '#/lib/format/agreements'
import { formatDay, formatMoney, toNumber } from '#/lib/format/format'

/** Each volume commitment's spend against its pro-rata target, and where it is heading. */
export function Commitments({
  commitments,
  currency,
}: {
  commitments: Array<CommitmentProgress>
  currency: string | null
}) {
  if (commitments.length === 0) {
    return null
  }
  return (
    <Card
      role="region"
      aria-label="Commitments"
      className="flex flex-col gap-5 p-5"
    >
      <h2 className="font-display text-base font-medium">Volume commitments</h2>
      {commitments.map((commitment) => {
        const progress = shareOf(commitment.spent, commitment.committed) ?? 0
        const behind =
          toNumber(commitment.spent) < toNumber(commitment.target_to_date)
        return (
          <div key={commitment.term_id} className="flex flex-col gap-2">
            <div className="flex flex-wrap items-baseline justify-between gap-2 text-sm">
              <span className="font-medium">{commitment.scope}</span>
              <span className="text-xs text-muted-foreground">
                {formatDay(commitment.period_start)} –{' '}
                {formatDay(commitment.period_end)}
              </span>
            </div>
            <Progress
              aria-label={`${commitment.scope}: ${progress}% of the commitment`}
              value={Math.min(100, progress)}
            />
            <p className="text-sm text-muted-foreground">
              <span className="font-medium text-foreground">
                {formatMoney(commitment.spent, currency)}
              </span>{' '}
              of {formatMoney(commitment.committed, currency)} ·{' '}
              <span className={behind ? 'text-warning' : 'text-success'}>
                {behind ? 'behind' : 'on track for'} the{' '}
                {formatMoney(commitment.target_to_date, currency)} due by today
              </span>{' '}
              · heading for {formatMoney(commitment.forecast, currency)}
            </p>
            {commitment.tier_reached !== null ||
            commitment.next_tier !== null ? (
              <p className="text-xs text-muted-foreground">
                {commitment.tier_reached !== null
                  ? `Rebate tier reached at ${formatMoney(commitment.tier_reached, currency)}. `
                  : ''}
                {commitment.next_tier !== null
                  ? `Next tier at ${formatMoney(commitment.next_tier, currency)}.`
                  : ''}
              </p>
            ) : null}
          </div>
        )
      })}
    </Card>
  )
}
