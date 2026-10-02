import { describe, expect, it } from 'vitest'
import {
  applyAlternativeFilterChange,
  isFiltered,
  validateAlternativeSearch,
} from './alternative-search'

describe('alternative search', () => {
  it('keeps known values and drops the rest', () => {
    expect(
      validateAlternativeSearch({
        source: 'marketplace',
        match: 'nearly',
        item_class: 'material',
        page: '3',
      }),
    ).toEqual({
      company_id: undefined,
      source: 'marketplace',
      match: undefined,
      item_class: 'material',
      page: 3,
    })
  })

  it('returns to the first page when a filter changes', () => {
    expect(
      applyAlternativeFilterChange({ page: 4 }, { match: 'exact' }),
    ).toEqual({ page: undefined, match: 'exact' })
    expect(isFiltered({ page: 2 })).toBe(false)
    expect(isFiltered({ match: 'exact' })).toBe(true)
  })
})
