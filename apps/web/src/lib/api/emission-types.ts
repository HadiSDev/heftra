import type { Money } from './types'

/** Whether a voucher's emissions were estimated, and if not, why. */
export type EmissionsStatus =
  | 'estimated'
  | 'partial'
  | 'no_spend'
  | 'no_lines'
  | 'unmatched'
  | 'no_factor'
  | 'unconverted'
  | 'no_factor_set'

/** Who chose a line's emission sector. */
export type EmissionSectorSource = 'ai' | 'human'

/** An emission sector of the active factor set. */
export interface EmissionSectorRead {
  id: string
  code: string
  name: string
}

/** The factor set every emission figure comes from, and how it must be credited. */
export interface FactorSetRead {
  source: string
  version: string
  currency: string
  price_year: number
  price_basis: string
  attribution: string
}

/** How much of one base currency's posted spend the estimate covers. */
export interface EmissionsSpendRow {
  currency: string
  posted_spend: Money
  estimated_spend: Money
}

/** `GET /erp-entries/vouchers/emissions`: the listed vouchers' estimated emissions. */
export interface EmissionsSummaryRead {
  /** Null when no emission factors are imported. */
  factor_set: FactorSetRead | null
  kg_co2e: Money | null
  spend: Array<EmissionsSpendRow>
  vouchers_by_status: Partial<Record<EmissionsStatus, number>>
}
