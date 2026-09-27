import { Link } from '@tanstack/react-router'
import { ExternalLink } from 'lucide-react'
import {
  Badge,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '#/components/ui'
import type {
  FindingRead,
  FindingReview as Review,
} from '#/lib/api/agreement-types'
import {
  FINDING_KIND_LABELS,
  FINDING_KIND_VARIANTS,
  REVIEW_LABELS,
} from '#/lib/format/agreements'
import { formatDay, formatMoney } from '#/lib/format/format'
import { FindingReview } from './finding-review'

export interface FindingsTableProps {
  findings: Array<FindingRead>
  companyId: string
  canReview: boolean
  onReview: (findingId: string, review: Review) => Promise<void>
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
    <span className="font-medium">
      {formatMoney(finding.amount, finding.currency)}
    </span>
  )
}

/** Findings with what was bought, what it cost against the agreement, why, and their review. */
export function FindingsTable({
  findings,
  companyId,
  canReview,
  onReview,
}: FindingsTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Finding</TableHead>
          <TableHead>Date</TableHead>
          <TableHead>Bought</TableHead>
          <TableHead className="text-right">Amount</TableHead>
          <TableHead>Why</TableHead>
          <TableHead>Review</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {findings.map((finding) => (
          <TableRow
            key={finding.id}
            className={
              finding.review_status === 'open' ? undefined : 'opacity-70'
            }
          >
            <TableCell>
              <Badge variant={FINDING_KIND_VARIANTS[finding.kind]}>
                {FINDING_KIND_LABELS[finding.kind]}
              </Badge>
            </TableCell>
            <TableCell className="whitespace-nowrap">
              {formatDay(finding.spent_on)}
            </TableCell>
            <TableCell className="min-w-48">
              <div className="font-medium">{finding.item ?? '—'}</div>
              <div className="text-xs text-muted-foreground">
                {finding.supplier_name ?? 'Unknown supplier'}
              </div>
            </TableCell>
            <TableCell className="text-right whitespace-nowrap tabular-nums">
              <Amount finding={finding} />
            </TableCell>
            <TableCell className="max-w-md text-sm">
              <p>{finding.reason}</p>
              {finding.voucher_id ? (
                <Link
                  to="/invoice-lines"
                  search={{
                    company_id: companyId,
                    voucher: finding.voucher_id,
                    tab: 'lines',
                  }}
                  className="mt-1 inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                >
                  Open the voucher
                  <ExternalLink className="size-3" aria-hidden="true" />
                </Link>
              ) : null}
            </TableCell>
            <TableCell className="whitespace-nowrap">
              <div className="flex flex-col items-start gap-1">
                {finding.review_status !== 'open' ? (
                  <span className="text-xs text-muted-foreground">
                    {REVIEW_LABELS[finding.review_status]}
                    {finding.reviewed_by_name
                      ? ` by ${finding.reviewed_by_name}`
                      : ''}
                    {finding.review_note ? `: ${finding.review_note}` : ''}
                  </span>
                ) : null}
                {canReview && finding.kind !== 'compliant' ? (
                  <FindingReview
                    finding={finding}
                    onReview={(review) => onReview(finding.id, review)}
                  />
                ) : null}
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
