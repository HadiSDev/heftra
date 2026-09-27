import type { Money } from './types'

/** A factor set as system admins manage it. */
export interface AdminFactorSetRead {
  id: string
  source: string
  version: string
  classification: string
  currency: string
  price_year: number
  price_basis: string
  attribution: string
  sectors: number
  factors: number
  imported_at: string
  active: boolean
}

/** A price index a factor set's currency is deflated with, and how much of it is stored. */
export interface AdminPriceIndexRead {
  series: string
  label: string
  currency: string
  months: number
  latest_month: string | null
  base_year: number | null
  base_average: Money | null
}

/** One company's lines by emission sector: `ai` includes `needs_review`. */
export interface SectorCoverageRow {
  company_id: string
  company_name: string
  organization_name: string
  lines: number
  ai: number
  human: number
  needs_review: number
  unmatched: number
}

/** `GET /admin/emission-factors`. */
export interface EmissionFactorsStatusRead {
  sets: Array<AdminFactorSetRead>
  price_indices: Array<AdminPriceIndexRead>
  coverage: Array<SectorCoverageRow>
}

export interface FactorSetActivationRead {
  factor_set: AdminFactorSetRead
  previous_version: string | null
  rematch_needed: boolean
}

export type ReferenceImportKind = 'factor_workbook' | 'price_index'

export type ReferenceImportStatus =
  'queued' | 'running' | 'succeeded' | 'failed'

/** A workbook upload or price index refresh, and its outcome once run. */
export interface ReferenceImportRead {
  id: string
  kind: ReferenceImportKind
  status: ReferenceImportStatus
  /** The uploaded file's name, or the series id. */
  subject: string
  activate: boolean
  requested_by: string
  requested_by_name: string | null
  requested_at: string
  started_at: string | null
  finished_at: string | null
  result: Record<string, unknown> | null
  error: string | null
}
