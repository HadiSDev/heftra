import type { TermRead } from '#/lib/api/agreement-types'
import { formatMoney } from '#/lib/format/format'
import { formatPercent } from '#/lib/format/agreements'

/** What a term says, in a line or two. */
export function TermSummary({ term }: { term: TermRead }) {
  if (term.kind === 'agreed_price') {
    return (
      <p>
        <span className="font-medium">{term.item ?? term.scope}</span> at{' '}
        <span className="font-medium tabular-nums">
          {term.unit_price !== null
            ? formatMoney(term.unit_price, term.currency)
            : '—'}
        </span>{' '}
        per {term.unit ?? 'unit'}
      </p>
    )
  }
  if (term.kind === 'discount') {
    return (
      <p>
        <span className="font-medium">
          {formatPercent(term.discount_percent)}
        </span>{' '}
        off {term.scope}
      </p>
    )
  }
  if (term.kind === 'volume_commitment') {
    return (
      <div className="flex flex-col gap-1">
        <p>
          <span className="font-medium tabular-nums">
            {term.commitment_amount !== null
              ? formatMoney(term.commitment_amount, term.currency)
              : '—'}
          </span>{' '}
          on {term.scope}
          {term.commitment_period ? ` per ${term.commitment_period}` : ''}
        </p>
        {(term.tiers ?? []).length > 0 ? (
          <p className="text-xs text-muted-foreground">
            Rebates:{' '}
            {(term.tiers ?? [])
              .map(
                (tier) =>
                  `${formatPercent(tier.rebate_percent)} from ${formatMoney(tier.threshold, term.currency)}`,
              )
              .join(', ')}
          </p>
        ) : null}
      </div>
    )
  }
  return (
    <p>
      <span className="font-medium">{term.scope}</span> must be bought from this
      supplier
      {term.conditions ? (
        <span className="text-muted-foreground"> — {term.conditions}</span>
      ) : null}
    </p>
  )
}
