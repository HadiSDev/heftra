import type { Money } from '#/lib/api/types'
import { toNumber } from './format'

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
