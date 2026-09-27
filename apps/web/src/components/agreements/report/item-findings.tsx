import { Link } from '@tanstack/react-router'
import { ExternalLink } from 'lucide-react'
import { cn } from '#/components/ui'
import type {
  FindingRead,
  FindingReview as Review,
  FindingSeverity,
} from '#/lib/api/agreement-types'
import { formatDay } from '#/lib/format/format'
import { FindingEntry } from './finding-entry'

const EDGES: Record<FindingSeverity, string> = {
  rule_break: 'border-l-destructive',
  warning: 'border-l-warning',
  info: 'border-l-border',
}

const RANK: Record<FindingSeverity, number> = {
  rule_break: 0,
  warning: 1,
  info: 2,
}

export interface ItemFindingsProps {
  findings: Array<FindingRead>
  companyId: string
  canReview: boolean
  onReview: (findingId: string, review: Review) => Promise<void>
}

function edge(findings: Array<FindingRead>): string {
  const open = findings.filter((finding) => finding.review_status === 'open')
  if (open.length === 0) {
    return 'border-l-border'
  }
  if (open.every((finding) => finding.kind === 'compliant')) {
    return 'border-l-success'
  }
  const worst = open.reduce((a, b) =>
    RANK[b.severity] < RANK[a.severity] ? b : a,
  )
  return EDGES[worst.severity]
}

/** An item that was bought, with every finding against it. */
export function ItemFindings({
  findings,
  companyId,
  canReview,
  onReview,
}: ItemFindingsProps) {
  const [first] = findings
  return (
    <li
      className={cn(
        'flex flex-col gap-3 border-l-4 py-4 pr-6 pl-5',
        edge(findings),
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-x-6 gap-y-1">
        <div className="min-w-0 flex-1">
          <p
            className="line-clamp-2 font-medium"
            title={first.item ?? undefined}
          >
            {first.item ?? '—'}
          </p>
          <p className="text-xs text-muted-foreground">
            {formatDay(first.spent_on)} ·{' '}
            {first.supplier_name ?? 'Unknown supplier'}
          </p>
        </div>
        {first.voucher_id ? (
          <Link
            to="/invoice-lines"
            search={{
              company_id: companyId,
              voucher: first.voucher_id,
              tab: 'lines',
            }}
            className="inline-flex items-center gap-1 text-xs font-medium whitespace-nowrap text-primary hover:underline"
          >
            Open the voucher
            <ExternalLink className="size-3" aria-hidden="true" />
          </Link>
        ) : null}
      </div>
      <ul className="flex flex-col gap-3">
        {findings.map((finding) => (
          <FindingEntry
            key={finding.id}
            finding={finding}
            canReview={canReview}
            onReview={(review) => onReview(finding.id, review)}
          />
        ))}
      </ul>
    </li>
  )
}
