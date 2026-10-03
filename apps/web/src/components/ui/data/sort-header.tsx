import { ArrowDown, ArrowUp, ArrowUpDown } from 'lucide-react'
import { cn } from '../cn'
import { TableHead } from './table'

export type SortOrder = 'asc' | 'desc'

export interface SortHeaderProps<TColumn extends string> {
  label: string
  column: TColumn
  /** The column the table is currently sorted by. */
  sort: TColumn
  order: SortOrder
  onSort: (column: TColumn) => void
  align?: 'left' | 'right'
  /** When false the header is a plain label. */
  sortable?: boolean
  colSpan?: number
}

function ariaSort(active: boolean, order: SortOrder) {
  if (!active) {
    return 'none'
  }
  return order === 'asc' ? 'ascending' : 'descending'
}

/** A column header that sorts the table by its column, and shows which way. */
export function SortHeader<TColumn extends string>({
  label,
  column,
  sort,
  order,
  onSort,
  align = 'left',
  sortable = true,
  colSpan,
}: SortHeaderProps<TColumn>) {
  const active = sortable && sort === column
  const Icon = active ? (order === 'asc' ? ArrowUp : ArrowDown) : ArrowUpDown

  return (
    <TableHead
      aria-sort={sortable ? ariaSort(active, order) : undefined}
      colSpan={colSpan}
      className={cn(align === 'right' && 'text-right')}
    >
      {sortable ? (
        <button
          type="button"
          onClick={() => onSort(column)}
          className={cn(
            'inline-flex items-center gap-1 rounded-sm uppercase outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring',
            active && 'text-foreground',
          )}
        >
          {label}
          <Icon
            aria-hidden="true"
            className={cn('size-3.5', !active && 'opacity-40')}
          />
        </button>
      ) : (
        label
      )}
    </TableHead>
  )
}
