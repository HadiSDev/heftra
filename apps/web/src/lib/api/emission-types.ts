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
/** The price index a factor set's estimates are deflated with. */
export interface PriceIndexRead {
  series: string
  label: string
  latest_month: string | null
}

export interface FactorSetRead {
  source: string
  version: string
  currency: string
  price_year: number
  price_basis: string
  attribution: string
  /** Null when estimates are not adjusted for inflation. */
  price_index: PriceIndexRead | null
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

/** converted × base_index ÷ index = deflated, in `base_year` money. */
export interface EmissionDeflationRead {
  series: string
  label: string
  /** The month whose index value was used. */
  month: string
  index: Money
  base_year: number
  base_index: Money
  deflated: Money
}

/** How a line's emissions were multiplied out: spend × rate = converted, deflated, × factor = kg. */
export interface EmissionCalculationRead {
  spend: Money
  currency: string
  rate: Money
  rate_date: string
  converted: Money
  /** Null when the estimate is not adjusted for inflation. */
  deflation: EmissionDeflationRead | null
  factor: Money
  factor_currency: string
  /** The country code or region the factor is for. */
  factor_area: string
  sector: EmissionSectorRead | null
  kg_co2e: Money
}
