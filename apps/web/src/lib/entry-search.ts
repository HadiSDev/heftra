import type { VoucherSelection } from './api/entries'
import type {
  DocumentFilter,
  EntryFilters,
  LineOrigin,
  SortOrder,
  VoucherSort,
  VoucherTab,
} from './api/types'
import { oneOf, sortOrder } from './sorting'
import type { SortState } from './sorting'

/** Read one search key, dropping empty values. */
function str(value: unknown): string | undefined {
  return typeof value === 'string' && value !== '' ? value : undefined
}

const VOUCHER_TABS: ReadonlyArray<VoucherTab> = [
  'lines',
  'details',
  'postings',
  'activity',
]

/** The line provenances worth filtering by. */
export const LINE_ORIGINS: ReadonlyArray<LineOrigin> = [
  'document_ai',
  'erp',
  'entry_fallback',
  'human',
]

/** Read the origin, ignoring unknown values. */
function origin(value: unknown): LineOrigin | undefined {
  return typeof value === 'string' &&
    (LINE_ORIGINS as ReadonlyArray<string>).includes(value)
    ? (value as LineOrigin)
    : undefined
}

/** The document states worth filtering by. */
export const DOCUMENT_FILTERS: ReadonlyArray<DocumentFilter> = [
  'failed',
  'mismatch',
]

/** Read the document filter, ignoring unknown values. */
function document(value: unknown): DocumentFilter | undefined {
  return typeof value === 'string' &&
    (DOCUMENT_FILTERS as ReadonlyArray<string>).includes(value)
    ? (value as DocumentFilter)
    : undefined
}

/** Read a flag that is only ever on, from `true` or `"true"`. */
function flag(value: unknown): true | undefined {
  return value === true || value === 'true' ? true : undefined
}

/** Read the tab, ignoring unknown values. */
function tab(value: unknown): VoucherTab | undefined {
  return typeof value === 'string' &&
    (VOUCHER_TABS as ReadonlyArray<string>).includes(value)
    ? (value as VoucherTab)
    : undefined
}

/** The columns the voucher list sorts by. */
const VOUCHER_SORTS: ReadonlyArray<VoucherSort> = [
  'accounting_date',
  'voucher_number',
  'vendor_name',
  'amount',
]

/** Parse the Entries route's search params. */
export function validateEntrySearch(
  search: Record<string, unknown>,
): EntryFilters {
  const page = Number(search.page)
  return {
    company_id: str(search.company_id),
    entry_type: str(search.entry_type),
    status: str(search.status),
    vendor_id: str(search.vendor_id),
    origin: origin(search.origin),
    needs_review: flag(search.needs_review),
    document: document(search.document),
    from: str(search.from),
    to: str(search.to),
    sort: oneOf(search.sort, VOUCHER_SORTS),
    order: sortOrder(search.order),
    page: Number.isInteger(page) && page > 1 ? page : undefined,
    voucher: str(search.voucher),
    entry: str(search.entry),
    tab: tab(search.tab),
  }
}

/** Apply a filter change. */
export function applyFilterChange(
  filters: EntryFilters,
  changes: Partial<EntryFilters>,
): EntryFilters {
  return {
    ...filters,
    ...changes,
    page: undefined,
    voucher: undefined,
    entry: undefined,
    tab: undefined,
  }
}

/** Apply a sort change, returning to the first page and leaving the voucher panel as it is. */
export function applySortChange(
  filters: EntryFilters,
  sort: SortState<VoucherSort>,
): EntryFilters {
  return { ...filters, ...sort, page: undefined }
}

/** The order a column sorts in when first chosen: suppliers A–Z, figures and dates largest first. */
export function defaultVoucherOrder(sort: VoucherSort): SortOrder {
  return sort === 'vendor_name' ? 'asc' : 'desc'
}

/** The sort in effect: the URL's, else newest first; amount only when it can be ordered. */
export function resolveVoucherSort(
  filters: EntryFilters,
  amountSortable: boolean,
): SortState<VoucherSort> {
  const requested =
    filters.sort === 'amount' && !amountSortable ? undefined : filters.sort
  if (requested === undefined) {
    return { sort: 'accounting_date', order: 'desc' }
  }
  return {
    sort: requested,
    order: filters.order ?? defaultVoucherOrder(requested),
  }
}

/** Apply a request to open (or close) the voucher panel. */
export function applyVoucherSelection(
  filters: EntryFilters,
  selection: VoucherSelection,
): EntryFilters {
  const open = selection.voucher !== undefined || selection.entry !== undefined
  return {
    ...filters,
    voucher: selection.voucher,
    entry: selection.entry,
    tab: open ? (selection.tab ?? filters.tab) : undefined,
  }
}

/** Entry types the API never lists. */
const EXCLUDED_ENTRY_TYPES: ReadonlyArray<string> = ['payment']

/** The entry types worth offering as a filter. */
export function listableEntryTypes(types: Iterable<string>): Array<string> {
  return [...new Set(types)]
    .filter((t) => !EXCLUDED_ENTRY_TYPES.includes(t))
    .sort()
}
