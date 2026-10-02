import type {
  AlternativeFilters,
  AlternativeMatch,
  AlternativeSource,
  ItemClass,
} from './api/alternative-types'

const SOURCES: ReadonlyArray<AlternativeSource> = [
  'history',
  'benchmark',
  'marketplace',
]
const MATCHES: ReadonlyArray<AlternativeMatch> = ['exact', 'equivalent']
const CLASSES: ReadonlyArray<ItemClass> = [
  'material',
  'part',
  'finished_good',
  'service',
]

function oneOf<T extends string>(
  value: unknown,
  allowed: ReadonlyArray<T>,
): T | undefined {
  return typeof value === 'string' &&
    (allowed as ReadonlyArray<string>).includes(value)
    ? (value as T)
    : undefined
}

/** Parse the Alternatives route's search params, dropping unknown values. */
export function validateAlternativeSearch(
  search: Record<string, unknown>,
): AlternativeFilters {
  const page = Number(search.page)
  return {
    company_id:
      typeof search.company_id === 'string' && search.company_id !== ''
        ? search.company_id
        : undefined,
    source: oneOf(search.source, SOURCES),
    match: oneOf(search.match, MATCHES),
    item_class: oneOf(search.item_class, CLASSES),
    page: Number.isInteger(page) && page > 1 ? page : undefined,
  }
}

/** Apply a filter change, returning to the first page. */
export function applyAlternativeFilterChange(
  filters: AlternativeFilters,
  changes: Partial<AlternativeFilters>,
): AlternativeFilters {
  return { ...filters, ...changes, page: undefined }
}

/** Whether any filter narrows the list. */
export function isFiltered(filters: AlternativeFilters): boolean {
  return (
    filters.company_id !== undefined ||
    filters.source !== undefined ||
    filters.match !== undefined ||
    filters.item_class !== undefined
  )
}
