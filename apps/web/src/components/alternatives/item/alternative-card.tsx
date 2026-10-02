import { ExternalLink, TriangleAlert } from 'lucide-react'
import { Link } from '@tanstack/react-router'
import { Badge, Card, cn } from '#/components/ui'
import type {
  AlternativeRead,
  AlternativeReview as Review,
  PricingUnit,
} from '#/lib/api/alternative-types'
import {
  DISMISS_REASON_LABELS,
  MATCH_LABELS,
  MATCH_VARIANTS,
  REVIEW_LABELS,
  SOURCE_LABELS,
  originText,
  perUnit,
} from '#/lib/format/alternatives'
import { formatMoney, toNumber } from '#/lib/format/format'
import { AlternativeReview } from './alternative-review'
import { AttributeTable } from './attribute-table'

function reviewText(alternative: AlternativeRead): string {
  const reason = alternative.dismiss_reason
    ? ` · ${DISMISS_REASON_LABELS[alternative.dismiss_reason]}`
    : ''
  const by = alternative.reviewed_by_name
    ? ` by ${alternative.reviewed_by_name}`
    : ''
  const note = alternative.review_note ? `: ${alternative.review_note}` : ''
  return `${REVIEW_LABELS[alternative.review_status]}${reason}${by}${note}`
}

export interface AlternativeCardProps {
  alternative: AlternativeRead
  pricingUnit: PricingUnit | null
  canReview: boolean
  onReview: (review: Review) => Promise<void>
}

/** One alternative: what it saves, where it was found, what it would break, and how its
 * attributes compare. */
export function AlternativeCard({
  alternative,
  pricingUnit,
  canReview,
  onReview,
}: AlternativeCardProps) {
  const reviewed = alternative.review_status !== 'open'
  const url = alternative.origin.url
  return (
    <Card
      role="article"
      aria-label={alternative.name}
      className={cn('flex flex-col gap-4 p-5', reviewed && 'opacity-70')}
    >
      <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_auto]">
        <div className="flex min-w-0 flex-col gap-1.5">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={MATCH_VARIANTS[alternative.match]}>
              {MATCH_LABELS[alternative.match]}
            </Badge>
            <span className="text-xs font-medium text-muted-foreground">
              {SOURCE_LABELS[alternative.source]}
            </span>
          </div>
          <h3 className="font-medium">
            {url ? (
              <a
                href={url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 hover:underline"
              >
                {alternative.name}
                <ExternalLink className="size-3.5" aria-hidden="true" />
              </a>
            ) : (
              alternative.name
            )}
          </h3>
          <p className="text-sm text-muted-foreground">
            {originText(alternative)}
          </p>
        </div>
        <div className="flex flex-col sm:items-end">
          <span className="font-display text-2xl font-semibold text-success tabular-nums">
            {alternative.saving_yearly !== null
              ? formatMoney(alternative.saving_yearly, alternative.currency)
              : `${Math.round(toNumber(alternative.saving_percent))}% less`}
          </span>
          <span className="text-xs text-muted-foreground">
            {alternative.saving_yearly !== null
              ? `a year · ${Math.round(toNumber(alternative.saving_percent))}% less`
              : 'per unit'}
          </span>
          <span className="mt-1 text-sm tabular-nums">
            {perUnit(alternative.unit_price, alternative.currency, pricingUnit)}
          </span>
        </div>
      </div>

      {alternative.agreement_notes.map((note) => (
        <p
          key={`${note.term_id}-${note.kind}`}
          className="flex items-start gap-2 rounded-md bg-warning/10 px-3 py-2 text-sm"
        >
          <TriangleAlert
            className="mt-0.5 size-4 shrink-0 text-warning"
            aria-hidden="true"
          />
          <span>
            {note.text}{' '}
            <Link
              to="/agreements/$agreementId"
              params={{ agreementId: note.agreement_id }}
              className="font-medium hover:underline"
            >
              Open the agreement
            </Link>
          </span>
        </p>
      ))}

      <AttributeTable comparison={alternative.comparison} />

      {alternative.origin.shipping || alternative.origin.availability ? (
        <p className="text-xs text-muted-foreground">
          {[alternative.origin.availability, alternative.origin.shipping]
            .filter(Boolean)
            .join(' · ')}
          . Shipping isn’t included in the price.
        </p>
      ) : null}

      <div className="flex flex-wrap items-center justify-between gap-2">
        {reviewed ? (
          <p className="text-xs text-muted-foreground">
            {reviewText(alternative)}
          </p>
        ) : (
          <span />
        )}
        {canReview ? (
          <AlternativeReview alternative={alternative} onReview={onReview} />
        ) : null}
      </div>
    </Card>
  )
}
