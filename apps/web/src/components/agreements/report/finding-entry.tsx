import * as React from 'react'
import { Badge, cn } from '#/components/ui'
import type {
  FindingRead,
  FindingReview as Review,
} from '#/lib/api/agreement-types'
import {
  FINDING_KIND_LABELS,
  FINDING_KIND_VARIANTS,
  REVIEW_LABELS,
} from '#/lib/format/agreements'
import { formatMoney } from '#/lib/format/format'
import { FindingReview } from './finding-review'

const LONG_REASON = 180

export interface FindingEntryProps {
  finding: FindingRead
  canReview: boolean
  onReview: (review: Review) => Promise<void>
}

function Amount({ finding }: { finding: FindingRead }) {
  if (finding.kind === 'compliant' || finding.kind === 'price_unverifiable') {
    return (
      <span className="text-muted-foreground">
        {formatMoney(finding.line_amount, finding.currency)}
      </span>
    )
  }
  return (
    <span className="font-display text-base font-semibold">
      {formatMoney(finding.amount, finding.currency)}
    </span>
  )
}

function Reason({ text }: { text: string }) {
  const [expanded, setExpanded] = React.useState(false)
  const long = text.length > LONG_REASON
  return (
    <div className="text-sm text-muted-foreground">
      <p className={cn(long && !expanded && 'line-clamp-2')}>{text}</p>
      {long ? (
        <button
          type="button"
          className="mt-0.5 text-xs font-medium text-foreground hover:underline"
          aria-expanded={expanded}
          onClick={() => {
            setExpanded(!expanded)
          }}
        >
          {expanded ? 'Show less' : 'Show more'}
        </button>
      ) : null}
    </div>
  )
}

/** One finding on a bought item: its kind and amount, why, and its review. */
export function FindingEntry({
  finding,
  canReview,
  onReview,
}: FindingEntryProps) {
  const reviewed = finding.review_status !== 'open'
  return (
    <li
      className={cn(
        'grid gap-x-6 gap-y-1.5 sm:grid-cols-[minmax(0,1fr)_auto]',
        reviewed && 'opacity-70',
      )}
    >
      <div className="flex min-w-0 flex-col gap-1">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={FINDING_KIND_VARIANTS[finding.kind]}>
            {FINDING_KIND_LABELS[finding.kind]}
          </Badge>
          <span className="whitespace-nowrap tabular-nums">
            <Amount finding={finding} />
          </span>
        </div>
        <Reason text={finding.reason} />
        {reviewed ? (
          <p className="text-xs text-muted-foreground">
            {REVIEW_LABELS[finding.review_status]}
            {finding.reviewed_by_name ? ` by ${finding.reviewed_by_name}` : ''}
            {finding.review_note ? `: ${finding.review_note}` : ''}
          </p>
        ) : null}
      </div>
      {canReview && finding.kind !== 'compliant' ? (
        <div className="sm:pt-0.5">
          <FindingReview finding={finding} onReview={onReview} />
        </div>
      ) : null}
    </li>
  )
}
