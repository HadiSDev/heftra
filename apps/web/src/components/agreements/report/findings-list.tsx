import type {
  FindingRead,
  FindingReview as Review,
} from '#/lib/api/agreement-types'
import { byItem } from '#/lib/agreements/findings'
import { ItemFindings } from './item-findings'

export interface FindingsListProps {
  findings: Array<FindingRead>
  companyId: string
  canReview: boolean
  onReview: (findingId: string, review: Review) => Promise<void>
}

/** Each item bought, with its findings. */
export function FindingsList({
  findings,
  companyId,
  canReview,
  onReview,
}: FindingsListProps) {
  return (
    <ul className="divide-y border-t">
      {byItem(findings).map((group) => (
        <ItemFindings
          key={group[0].invoice_line_id}
          findings={group}
          companyId={companyId}
          canReview={canReview}
          onReview={onReview}
        />
      ))}
    </ul>
  )
}
