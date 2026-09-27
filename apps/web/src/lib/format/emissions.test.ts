import { describe, expect, it } from 'vitest'
import {
  calculationSteps,
  formatEmissions,
  formatEmissionsAmount,
} from './emissions'

describe('formatEmissions', () => {
  it('shows kilograms below a tonne, to three significant figures', () => {
    expect(formatEmissions('72.500')).toBe('72.5 kg CO₂e')
    expect(formatEmissions('145.678')).toBe('146 kg CO₂e')
    expect(formatEmissions('0.123')).toBe('0.123 kg CO₂e')
  })

  it('shows tonnes to one decimal from a tonne up', () => {
    expect(formatEmissions('12437')).toBe('12.4 t CO₂e')
    expect(formatEmissions(1000)).toBe('1.0 t CO₂e')
  })

  it('keeps the sign of a credit note', () => {
    expect(formatEmissions('-5.8')).toBe('-5.8 kg CO₂e')
  })
})

describe('calculationSteps', () => {
  it('writes out the spend, the conversion and the factor, ending in the result', () => {
    const steps = calculationSteps({
      spend: '1000.00',
      currency: 'DKK',
      rate: '0.145',
      rate_date: '2025-07-01',
      converted: '145.00',
      factor: '0.5',
      factor_currency: 'USD',
      factor_area: 'DE',
      sector: { id: 's1', code: '518200', name: 'Hosting' },
      kg_co2e: '72.500',
    }).map((step) => step.replace(/\s/g, ' '))

    expect(steps).toEqual([
      'Share of the voucher’s spend: DKK 1,000.00',
      '× 0.145 DKK→USD on 1 Jul 2025 = US$145.00',
      '× 0.5 kg CO₂e per USD (Hosting, factor for DE) = 72.5 kg CO₂e',
    ])
  })
})

describe('formatEmissionsAmount', () => {
  it('leaves out CO₂e for a column already headed with it', () => {
    expect(formatEmissionsAmount('19.6')).toBe('19.6 kg')
    expect(formatEmissionsAmount('1234')).toBe('1.2 t')
  })
})
