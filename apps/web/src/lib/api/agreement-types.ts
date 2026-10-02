import type { Money, PipelineRunStatus } from './types'
import type { ReportPeriods } from './spend-report-types'

export type AgreementStatus =
  'pending' | 'reading' | 'review' | 'active' | 'failed'

export type AgreementTermKind =
  'preferred_supplier' | 'agreed_price' | 'discount' | 'volume_commitment'

export type AgreementTermStatus = 'draft' | 'confirmed' | 'rejected'

export type FindingKind =
  | 'compliant'
  | 'off_contract'
  | 'overcharge'
  | 'missed_discount'
  | 'potential_saving'
  | 'price_unverifiable'

export type FindingSeverity = 'rule_break' | 'warning' | 'info'

export type FindingReviewStatus = 'open' | 'exception' | 'not_in_scope'

export interface TermQuote {
  text: string
  page: number | null
}

export interface RebateTier {
  threshold: Money
  rebate_percent: Money
}

/** The fields a term of any kind can carry; each kind uses its own. */
export interface TermFields {
  scope: string
  conditions: string | null
  item: string | null
  unit: string | null
  unit_price: Money | null
  discount_percent: Money | null
  commitment_amount: Money | null
  commitment_period: string | null
  tiers: Array<RebateTier> | null
  currency: string | null
  scope_category_ids: Array<string>
}

export interface TermRead extends TermFields {
  id: string
  agreement_id: string
  kind: AgreementTermKind
  status: AgreementTermStatus
  source: 'ai' | 'human'
  quotes: Array<TermQuote>
  confidence: Money | null
  created_at: string
  updated_at: string | null
}

export type TermCreate = Partial<TermFields> & {
  kind: AgreementTermKind
  scope: string
}

export type TermPatch = Partial<TermFields> & {
  status?: AgreementTermStatus
}

export interface AgreementSupplier {
  vendor_id: string
  name: string
}

/** An agreement in the list, with its open rule breaks. */
export interface AgreementSummaryRead {
  id: string
  company_id: string
  title: string
  reference: string | null
  supplier: AgreementSupplier | null
  supplier_name: string | null
  starts_on: string | null
  ends_on: string | null
  currency: string | null
  status: AgreementStatus
  expired: boolean
  read_error: string | null
  analysed_at: string | null
  created_at: string
  open_rule_breaks: number
  rule_break_amount: Money
  base_currency: string | null
}

/** The company's latest check of its spend against its agreements. */
export interface AgreementAnalysis {
  id: string
  status: PipelineRunStatus
  requested_at: string
  started_at: string | null
  finished_at: string | null
  error: string | null
  /** Terms whose candidates were capped in the last completed check. */
  capped_terms: number
  /** Whether the last completed check could search for similar items. */
  similarity_available: boolean
  /** Items the model could not judge in the last completed check. */
  unjudged_items: number
}

export interface AgreementRead extends AgreementSummaryRead {
  supplier_vat_number: string | null
  supplier_website: string | null
  summary: string | null
  read_at: string | null
  file: { filename: string; file_size: number | null }
  terms: Array<TermRead>
  analysis: AgreementAnalysis | null
}

export interface AgreementPatch {
  vendor_id?: string | null
  title?: string
  reference?: string | null
  starts_on?: string | null
  ends_on?: string | null
  currency?: string | null
}

export interface FindingRead {
  id: string
  agreement_id: string
  term_id: string
  term_kind: AgreementTermKind
  term_scope: string
  term_conditions: string | null
  kind: FindingKind
  severity: FindingSeverity
  amount: Money
  line_amount: Money
  currency: string | null
  expected: Money | null
  actual: Money | null
  quantity: Money | null
  reason: string
  judge_confidence: Money | null
  spent_on: string | null
  invoice_line_id: string
  invoice_id: string
  voucher_id: string | null
  item: string | null
  supplier_name: string | null
  from_supplier: boolean
  review_status: FindingReviewStatus
  review_note: string | null
  reviewed_by_name: string | null
  reviewed_at: string | null
}

export interface FindingReview {
  review_status: FindingReviewStatus
  note?: string | null
}

export interface FindingTotal {
  kind: FindingKind
  severity: FindingSeverity
  count: number
  amount: Money
}

export interface CommitmentProgress {
  term_id: string
  scope: string
  period_start: string
  period_end: string
  committed: Money
  spent: Money
  target_to_date: Money
  forecast: Money
  tier_reached: Money | null
  next_tier: Money | null
}

export interface AgreementReport {
  agreement_id: string
  analysed_at: string | null
  currency: string | null
  in_scope_spend: Money
  supplier_spend: Money
  totals: Array<FindingTotal>
  commitments: Array<CommitmentProgress>
  findings: {
    items: Array<FindingRead>
    page: number
    page_size: number
    total: number
  }
}

export interface OffContractSupplier {
  vendor_id: string | null
  name: string
  amount: Money
  count: number
}

/** `GET /reports/agreement-compliance`: the period's open rule breaks. */
export interface AgreementCompliance extends ReportPeriods {
  has_active_agreement: boolean
  currency: string | null
  open_rule_breaks: number
  rule_break_amount: Money
  off_contract_amount: Money
  overcharge_amount: Money
  top_suppliers: Array<OffContractSupplier>
}
