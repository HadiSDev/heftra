import type { EmissionCalculationRead } from '#/lib/api/emission-types'
import type { Money } from '#/lib/api/types'
import { formatDay, formatMoney, toNumber } from './format'

const kilograms = new Intl.NumberFormat('en-GB', {
  maximumSignificantDigits: 3,
})
const tonnes = new Intl.NumberFormat('en-GB', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
})

/** kg CO2e as people read it: kilograms below a tonne, tonnes to one decimal from there. */
export function formatEmissions(kg: Money): string {
  const value = toNumber(kg)
  if (Math.abs(value) >= 1000) {
    return `${tonnes.format(value / 1000)} t CO₂e`
  }
  return `${kilograms.format(value)} kg CO₂e`
}

const factorFormat = new Intl.NumberFormat('en-GB', {
  maximumSignificantDigits: 4,
})
const rateFormat = new Intl.NumberFormat('en-GB', {
  maximumSignificantDigits: 6,
})

/** The steps a line's emissions were multiplied out in, each as one readable sentence. */
export function calculationSteps(
  calculation: EmissionCalculationRead,
): Array<string> {
  const sector = calculation.sector ? `${calculation.sector.name}, ` : ''
  return [
    `Share of the voucher’s spend: ${formatMoney(calculation.spend, calculation.currency)}`,
    `× ${rateFormat.format(toNumber(calculation.rate))} ${calculation.currency}→${calculation.factor_currency} on ${formatDay(calculation.rate_date)} = ${formatMoney(calculation.converted, calculation.factor_currency)}`,
    `× ${factorFormat.format(toNumber(calculation.factor))} kg CO₂e per ${calculation.factor_currency} (${sector}factor for ${calculation.factor_area}) = ${formatEmissions(calculation.kg_co2e)}`,
  ]
}
