import { describe, expect, it } from 'vitest'
import type { FactorSetRead } from '#/lib/api/emission-types'
import {
  calculationSteps,
  emissionsMethod,
  formatEmissions,
  formatEmissionsAmount,
  priceIndexCoverage,
} from './emissions'

const CALCULATION = {
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
  deflation: null,
}

const FACTOR_SET: FactorSetRead = {
  source: 'open_ceda',
  version: 'CEDA 2025',
  currency: 'USD',
  price_year: 2023,
  price_basis: 'purchaser',
  attribution: 'CEDA by Watershed',
  price_index: null,
}

function readable(steps: Array<string>): Array<string> {
  return steps.map((step) => step.replace(/\s/g, ' '))
}

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
    expect(readable(calculationSteps(CALCULATION))).toEqual([
      'Share of the voucher’s spend: DKK 1,000.00',
      '× 0.145 DKK→USD on 1 Jul 2025 = US$145.00',
      '× 0.5 kg CO₂e per USD (Hosting, factor for DE) = 72.5 kg CO₂e',
    ])
  })

  it('puts the deflation to the price year between the conversion and the factor', () => {
    const steps = calculationSteps({
      ...CALCULATION,
      deflation: {
        series: 'CPIAUCSL',
        label: 'US CPI',
        month: '2026-08-01',
        index: '334.131',
        base_year: 2023,
        base_index: '304.7025',
        deflated: '132.23',
      },
      kg_co2e: '66.113',
    })

    expect(readable(steps)).toEqual([
      'Share of the voucher’s spend: DKK 1,000.00',
      '× 0.145 DKK→USD on 1 Jul 2025 = US$145.00',
      '× US CPI 2023 avg 304.70 ÷ Aug 2026 334.13 = US$132.23 in 2023 prices',
      '× 0.5 kg CO₂e per USD (Hosting, factor for DE) = 66.1 kg CO₂e',
    ])
  })
})

describe('emissionsMethod', () => {
  it('says when figures are not adjusted for inflation', () => {
    expect(emissionsMethod(FACTOR_SET)).toBe(
      'Spend-based estimate · CEDA 2025 · 2023 USD · not adjusted for inflation',
    )
    expect(priceIndexCoverage(FACTOR_SET)).toBeNull()
  })

  it('names the index figures are adjusted with, and how far it runs', () => {
    const adjusted = {
      ...FACTOR_SET,
      price_index: {
        series: 'CPIAUCSL',
        label: 'US CPI',
        latest_month: '2026-08-01',
      },
    }

    expect(emissionsMethod(adjusted)).toBe(
      'Spend-based estimate · CEDA 2025 · 2023 USD · adjusted with US CPI',
    )
    expect(priceIndexCoverage(adjusted)).toContain(
      'US CPI (CPIAUCSL) through Aug 2026',
    )
  })
})

describe('formatEmissionsAmount', () => {
  it('leaves out CO₂e for a column already headed with it', () => {
    expect(formatEmissionsAmount('19.6')).toBe('19.6 kg')
    expect(formatEmissionsAmount('1234')).toBe('1.2 t')
  })
})
