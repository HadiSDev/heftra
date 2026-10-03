import type { SortOrder } from '#/components/ui'

/** A table's sort: the column and which way. */
export interface SortState<C extends string> {
  sort: C
  order: SortOrder
}

const ORDERS: ReadonlyArray<SortOrder> = ['asc', 'desc']

/** The sort after a header is clicked: another column starts in its own order, the same
 * column turns around. */
export function nextSort<C extends string>(
  current: SortState<C>,
  column: C,
  defaultOrder: (column: C) => SortOrder,
): SortState<C> {
  if (column !== current.sort) {
    return { sort: column, order: defaultOrder(column) }
  }
  return { sort: column, order: current.order === 'asc' ? 'desc' : 'asc' }
}

/** A search param that is one of `allowed`, else undefined. */
export function oneOf<T extends string>(
  value: unknown,
  allowed: ReadonlyArray<T>,
): T | undefined {
  return typeof value === 'string' &&
    (allowed as ReadonlyArray<string>).includes(value)
    ? (value as T)
    : undefined
}

/** A search param that is a sort order, else undefined. */
export function sortOrder(value: unknown): SortOrder | undefined {
  return oneOf(value, ORDERS)
}
