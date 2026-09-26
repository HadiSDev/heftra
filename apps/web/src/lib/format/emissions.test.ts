import { describe, expect, it } from 'vitest'
import { formatEmissions } from './emissions'

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
