import type { EmissionsStatus } from '#/lib/api/emission-types'

/** Why a voucher's emissions could not be estimated, as a reader is told. */
export const EMISSIONS_STATUS_REASON: Record<EmissionsStatus, string> = {
  estimated: 'Estimated from every line',
  partial: 'Estimated from some lines; the others have no emission sector yet',
  no_spend: 'No net expense was posted',
  no_lines: 'The voucher has no invoice lines to estimate from',
  unmatched: 'No line has an emission sector yet',
  no_factor: 'No emission factor for the supplier’s or the company’s country',
  unconverted: 'No exchange rate for the voucher’s date',
  no_factor_set: 'No emission factors are imported',
}

/** The statuses that leave a voucher without any estimate. */
export const NOT_ESTIMATED: ReadonlyArray<EmissionsStatus> = [
  'unmatched',
  'no_lines',
  'no_factor',
  'unconverted',
  'no_spend',
  'no_factor_set',
]
