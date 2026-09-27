import type {
  AgreementStatus,
  AgreementSummaryRead,
  AgreementTermKind,
  FindingKind,
  FindingReviewStatus,
  FindingSeverity,
} from '#/lib/api/agreement-types'
import { toNumber } from './format'
import type { Money } from '#/lib/api/types'

export const TERM_KIND_LABELS: Record<AgreementTermKind, string> = {
  preferred_supplier: 'Preferred supplier',
  agreed_price: 'Agreed price',
  discount: 'Discount',
  volume_commitment: 'Volume commitment',
}

export const FINDING_KIND_LABELS: Record<FindingKind, string> = {
  off_contract: 'Off-contract purchase',
  overcharge: 'Overcharge',
  missed_discount: 'Missed discount',
  price_unverifiable: 'Price can’t be compared',
  potential_saving: 'Potential saving',
  compliant: 'Compliant',
}

export const REVIEW_LABELS: Record<FindingReviewStatus, string> = {
  open: 'Open',
  exception: 'Accepted exception',
  not_in_scope: 'Not in scope',
}

export type BadgeVariant =
  'default' | 'outline' | 'success' | 'warning' | 'destructive' | 'info'

export const SEVERITY_VARIANTS: Record<FindingSeverity, BadgeVariant> = {
  rule_break: 'destructive',
  warning: 'warning',
  info: 'default',
}

/** How an agreement's state reads in the list, expiry included. */
export function agreementStatus(agreement: AgreementSummaryRead): {
  label: string
  variant: BadgeVariant
} {
  const labels: Record<
    AgreementStatus,
    { label: string; variant: BadgeVariant }
  > = {
    pending: { label: 'Reading', variant: 'info' },
    reading: { label: 'Reading', variant: 'info' },
    review: { label: 'Needs review', variant: 'warning' },
    active: { label: 'Active', variant: 'success' },
    failed: { label: 'Couldn’t read', variant: 'destructive' },
  }
  if (agreement.status === 'active' && agreement.expired) {
    return { label: 'Expired', variant: 'outline' }
  }
  return labels[agreement.status]
}

const percentFormat = new Intl.NumberFormat('en-GB', {
  maximumFractionDigits: 1,
})

export function formatPercent(value: Money | null): string {
  if (value === null) {
    return '—'
  }
  return `${percentFormat.format(toNumber(value))}%`
}

/** The share `part` is of `whole`, as a whole percentage, or null for nothing. */
export function shareOf(part: Money, whole: Money): number | null {
  const total = toNumber(whole)
  if (total <= 0) {
    return null
  }
  return Math.round((toNumber(part) / total) * 100)
}
