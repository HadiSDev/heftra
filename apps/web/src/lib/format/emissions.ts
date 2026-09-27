import type {
  EmissionCalculationRead,
  EmissionDeflationRead,
  FactorSetRead,
} from '#/lib/api/emission-types'
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
  return `${formatEmissionsAmount(kg)} CO₂e`
}

/** The amount and unit alone, for a column already headed CO₂e. */
export function formatEmissionsAmount(kg: Money): string {
  const value = toNumber(kg)
  if (Math.abs(value) >= 1000) {
    return `${tonnes.format(value / 1000)} t`
  }
  return `${kilograms.format(value)} kg`
}

const factorFormat = new Intl.NumberFormat('en-GB', {
  maximumSignificantDigits: 4,
})
const rateFormat = new Intl.NumberFormat('en-GB', {
  maximumSignificantDigits: 6,
})

const indexFormat = new Intl.NumberFormat('en-GB', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})
const monthFormat = new Intl.DateTimeFormat('en-GB', {
  month: 'short',
  year: 'numeric',
  timeZone: 'UTC',
})

/** "Aug 2026" for an ISO date in that month. */
export function formatIndexMonth(value: string): string {
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? value : monthFormat.format(parsed)
}

function deflationStep(
  deflation: EmissionDeflationRead,
  currency: string,
): string {
  return `× ${deflation.label} ${deflation.base_year} avg ${indexFormat.format(toNumber(deflation.base_index))} ÷ ${formatIndexMonth(deflation.month)} ${indexFormat.format(toNumber(deflation.index))} = ${formatMoney(deflation.deflated, currency)} in ${deflation.base_year} prices`
}

/** The steps a line's emissions were multiplied out in, each as one readable sentence. */
export function calculationSteps(
  calculation: EmissionCalculationRead,
): Array<string> {
  const sector = calculation.sector ? `${calculation.sector.name}, ` : ''
  const deflation = calculation.deflation
  return [
    `Share of the voucher’s spend: ${formatMoney(calculation.spend, calculation.currency)}`,
    `× ${rateFormat.format(toNumber(calculation.rate))} ${calculation.currency}→${calculation.factor_currency} on ${formatDay(calculation.rate_date)} = ${formatMoney(calculation.converted, calculation.factor_currency)}`,
    ...(deflation
      ? [deflationStep(deflation, calculation.factor_currency)]
      : []),
    `× ${factorFormat.format(toNumber(calculation.factor))} kg CO₂e per ${calculation.factor_currency} (${sector}factor for ${calculation.factor_area}) = ${formatEmissions(calculation.kg_co2e)}`,
  ]
}

/** "Spend-based estimate · CEDA 2025 · 2023 USD · adjusted with US CPI", or "… · not adjusted for inflation". */
export function emissionsMethod(factorSet: FactorSetRead): string {
  const adjustment = factorSet.price_index
    ? `adjusted with ${factorSet.price_index.label}`
    : 'not adjusted for inflation'
  return `Spend-based estimate · ${factorSet.version} · ${factorSet.price_year} ${factorSet.currency} · ${adjustment}`
}

/** How far the index runs, for a hover on the method line; null when not adjusted. */
export function priceIndexCoverage(factorSet: FactorSetRead): string | null {
  const index = factorSet.price_index
  if (!index) {
    return null
  }
  const through = index.latest_month
    ? ` through ${formatIndexMonth(index.latest_month)}`
    : ''
  return `Spend is taken back to ${factorSet.price_year} prices with ${index.label} (${index.series})${through}. Later months use the latest published value.`
}
