import type {
  AgreementStatus,
  AgreementSummaryRead,
} from '#/lib/api/agreement-types'
import type { SortOrder } from '#/lib/api/types'
import { toNumber } from '#/lib/format/format'
import { oneOf, sortOrder } from '#/lib/sorting'
import type { SortState } from '#/lib/sorting'

/** What the agreements list can be sorted by; `created_at` is the list's own order. */
export type AgreementSort =
  | 'created_at'
  | 'title'
  | 'supplier'
  | 'starts_on'
  | 'status'
  | 'open_rule_breaks'

export interface AgreementListSearch {
  sort?: AgreementSort
  order?: SortOrder
}

type SortValue = string | number | null

const SORTS: ReadonlyArray<AgreementSort> = [
  'created_at',
  'title',
  'supplier',
  'starts_on',
  'status',
  'open_rule_breaks',
]

/** Statuses in the order they need attention: review first, then failed reads. */
const STATUS_RANK: Record<AgreementStatus, number> = {
  review: 0,
  failed: 1,
  pending: 2,
  reading: 2,
  active: 3,
}

const EXPIRED_RANK = 4

/** The agreements list's sort from the URL, ignoring anything else. */
export function validateAgreementListSearch(
  search: Record<string, unknown>,
): AgreementListSearch {
  return {
    sort: oneOf(search.sort, SORTS),
    order: sortOrder(search.order),
  }
}

/** The order a column sorts in when first chosen: text and status A–Z, the rest newest or
 * largest first. */
export function defaultAgreementOrder(sort: AgreementSort): SortOrder {
  return sort === 'title' || sort === 'supplier' || sort === 'status'
    ? 'asc'
    : 'desc'
}

/** The sort in effect: the URL's, else newest first. */
export function resolveAgreementSort(
  search: AgreementListSearch,
): SortState<AgreementSort> {
  const sort = search.sort ?? 'created_at'
  return { sort, order: search.order ?? defaultAgreementOrder(sort) }
}

function statusRank(agreement: AgreementSummaryRead): number {
  if (agreement.status === 'active' && agreement.expired) {
    return EXPIRED_RANK
  }
  return STATUS_RANK[agreement.status]
}

function sortValues(
  agreement: AgreementSummaryRead,
  sort: AgreementSort,
): Array<SortValue> {
  switch (sort) {
    case 'created_at':
      return [agreement.created_at]
    case 'title':
      return [agreement.title]
    case 'supplier':
      return [agreement.supplier?.name ?? agreement.supplier_name]
    case 'starts_on':
      return [agreement.starts_on]
    case 'status':
      return [statusRank(agreement)]
    case 'open_rule_breaks':
      if (agreement.status !== 'active') {
        return [null, null]
      }
      return [agreement.open_rule_breaks, toNumber(agreement.rule_break_amount)]
  }
}

function compareValue(a: SortValue, b: SortValue): number {
  if (typeof a === 'string' && typeof b === 'string') {
    return a.localeCompare(b, undefined, { sensitivity: 'base' })
  }
  return Number(a) - Number(b)
}

function compareValues(
  a: Array<SortValue>,
  b: Array<SortValue>,
  direction: number,
): number {
  for (let index = 0; index < a.length; index += 1) {
    const left = a[index]
    const right = b[index]
    if (left === right) {
      continue
    }
    if (left === null) {
      return 1
    }
    if (right === null) {
      return -1
    }
    const compared = compareValue(left, right)
    if (compared !== 0) {
      return compared * direction
    }
  }
  return 0
}

/** The agreements in the chosen order, blanks last, ties newest first. */
export function sortAgreements(
  agreements: Array<AgreementSummaryRead>,
  { sort, order }: SortState<AgreementSort>,
): Array<AgreementSummaryRead> {
  const direction = order === 'asc' ? 1 : -1
  return [...agreements].sort(
    (a, b) =>
      compareValues(sortValues(a, sort), sortValues(b, sort), direction) ||
      b.created_at.localeCompare(a.created_at) ||
      a.id.localeCompare(b.id),
  )
}
