import type { SortOrder } from '#/components/ui'
import type { ItemLineRead } from '#/lib/api/alternative-types'
import { toNumber } from '#/lib/format/format'
import type { SortState } from '#/lib/sorting'

/** The columns an item's spend lines sort by. */
export type ItemLineSort = 'date' | 'amount'

/** Newest first, as the lines arrive. */
export const DEFAULT_ITEM_LINE_SORT: SortState<ItemLineSort> = {
  sort: 'date',
  order: 'desc',
}

/** Both columns start largest or newest first. */
export function itemLineOrder(): SortOrder {
  return 'desc'
}

function key(line: ItemLineRead, sort: ItemLineSort): number | string | null {
  if (sort === 'date') {
    return line.invoice_date
  }
  return line.net_amount === null ? null : toNumber(line.net_amount)
}

function compare(a: number | string, b: number | string): number {
  if (a < b) {
    return -1
  }
  return a > b ? 1 : 0
}

/** The lines in the chosen order, lines without the value last either way. */
export function sortItemLines(
  lines: ReadonlyArray<ItemLineRead>,
  { sort, order }: SortState<ItemLineSort>,
): Array<ItemLineRead> {
  const direction = order === 'asc' ? 1 : -1
  return [...lines].sort((first, second) => {
    const a = key(first, sort)
    const b = key(second, sort)
    if (a === null || b === null) {
      return a === b ? 0 : a === null ? 1 : -1
    }
    return compare(a, b) * direction
  })
}
