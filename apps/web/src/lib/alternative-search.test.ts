import { describe, expect, it } from 'vitest'
import type { CompanyRead } from './api/types'
import { nextSort } from './sorting'
import {
  applyAlternativeFilterChange,
  canSortByUnitPrice,
  defaultOrder,
  isFiltered,
  resolveAlternativeSort,
  validateAlternativeSearch,
} from './alternative-search'

function company(id: string, base_currency: string): CompanyRead {
  return { id, base_currency } as CompanyRead
}

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
      sort: undefined,
      order: undefined,
      page: 3,
    })
  })

  it('keeps a known sort and order and drops the rest', () => {
    expect(
      validateAlternativeSearch({ sort: 'unit_price', order: 'asc' }),
    ).toMatchObject({ sort: 'unit_price', order: 'asc' })
    expect(
      validateAlternativeSearch({ sort: 'spend', order: 'sideways' }),
    ).toMatchObject({ sort: undefined, order: undefined })
  })

  it('sorts by the best saving, largest first, unless told otherwise', () => {
    expect(resolveAlternativeSort({}, true)).toEqual({
      sort: 'saving',
      order: 'desc',
    })
    expect(resolveAlternativeSort({ sort: 'name' }, true)).toEqual({
      sort: 'name',
      order: 'asc',
    })
    expect(
      resolveAlternativeSort({ sort: 'alternatives', order: 'asc' }, true),
    ).toEqual({ sort: 'alternatives', order: 'asc' })
  })

  it('starts a new column in its own order and turns the same one around', () => {
    const current = { sort: 'saving' as const, order: 'desc' as const }
    expect(nextSort(current, 'supplier', defaultOrder)).toEqual({
      sort: 'supplier',
      order: 'asc',
    })
    expect(nextSort(current, 'saving', defaultOrder)).toEqual({
      sort: 'saving',
      order: 'asc',
    })
  })

  it('sorts unit prices only within one base currency', () => {
    const companies = [company('dk', 'DKK'), company('eu', 'EUR')]
    expect(canSortByUnitPrice(companies, undefined)).toBe(false)
    expect(canSortByUnitPrice(companies, 'eu')).toBe(true)
    expect(
      resolveAlternativeSort({ sort: 'unit_price', order: 'asc' }, false),
    ).toEqual({ sort: 'saving', order: 'desc' })
  })

  it('returns to the first page when a filter or the sort changes', () => {
    expect(
      applyAlternativeFilterChange({ page: 4 }, { match: 'exact' }),
    ).toEqual({ page: undefined, match: 'exact' })
    expect(
      applyAlternativeFilterChange({ page: 4 }, { sort: 'name', order: 'asc' }),
    ).toEqual({ page: undefined, sort: 'name', order: 'asc' })
    expect(isFiltered({ page: 2 })).toBe(false)
    expect(isFiltered({ match: 'exact' })).toBe(true)
  })
})
