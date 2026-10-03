import type {
  AlternativeFilters,
  AlternativeMatch,
  AlternativeSort,
  AlternativeSource,
  ItemClass,
} from './api/alternative-types'
import type { CompanyRead, SortOrder } from './api/types'
import { oneOf, sortOrder } from './sorting'

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
const SORTS: ReadonlyArray<AlternativeSort> = [
  'saving',
  'name',
  'supplier',
  'unit_price',
  'alternatives',
]

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
    sort: oneOf(search.sort, SORTS),
    order: sortOrder(search.order),
    page: Number.isInteger(page) && page > 1 ? page : undefined,
  }
}

/** Apply a filter or sort change, returning to the first page. */
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

/** The order a column sorts in when first chosen: names A–Z, figures largest first. */
export function defaultOrder(sort: AlternativeSort): SortOrder {
  return sort === 'name' || sort === 'supplier' ? 'asc' : 'desc'
}

/** Whether the listed companies share one base currency, so unit prices can be ordered. */
export function canSortByUnitPrice(
  companies: Array<CompanyRead>,
  companyId: string | undefined,
): boolean {
  const listed =
    companyId === undefined
      ? companies
      : companies.filter((company) => company.id === companyId)
  return new Set(listed.map((company) => company.base_currency)).size <= 1
}

/** The sort in effect: the URL's, else the best yearly saving, largest first. */
export function resolveAlternativeSort(
  filters: AlternativeFilters,
  unitPriceSortable: boolean,
): { sort: AlternativeSort; order: SortOrder } {
  const requested =
    filters.sort === 'unit_price' && !unitPriceSortable
      ? undefined
      : filters.sort
  if (requested === undefined) {
    return { sort: 'saving', order: defaultOrder('saving') }
  }
  return { sort: requested, order: filters.order ?? defaultOrder(requested) }
}
