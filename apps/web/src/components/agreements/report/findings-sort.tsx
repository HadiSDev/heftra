import { ArrowDown, ArrowUp } from 'lucide-react'
import {
  Button,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '#/components/ui'
import { defaultFindingOrder } from '#/lib/agreement-search'
import type { FindingSort } from '#/lib/api/agreement-types'
import type { SortOrder } from '#/lib/api/types'
import { nextSort } from '#/lib/sorting'
import type { SortState } from '#/lib/sorting'

interface SortOption {
  value: FindingSort
  label: string
  /** How each order reads for this column. */
  orders: Record<SortOrder, string>
}

const OPTIONS: ReadonlyArray<SortOption> = [
  {
    value: 'severity',
    label: 'Severity',
    orders: { desc: 'Rule breaks first', asc: 'Least severe first' },
  },
  {
    value: 'amount',
    label: 'Amount',
    orders: { desc: 'Largest first', asc: 'Smallest first' },
  },
  {
    value: 'spent_on',
    label: 'Date',
    orders: { desc: 'Newest first', asc: 'Oldest first' },
  },
  {
    value: 'supplier',
    label: 'Supplier',
    orders: { asc: 'A–Z', desc: 'Z–A' },
  },
  {
    value: 'item',
    label: 'Item',
    orders: { asc: 'A–Z', desc: 'Z–A' },
  },
]

const ITEMS = OPTIONS.map((option) => ({
  value: option.value,
  label: option.label,
}))

export interface FindingsSortProps {
  sort: FindingSort
  order: SortOrder
  onSortChange: (next: SortState<FindingSort>) => void
}

/** Choose what the findings are sorted by, and turn the order around. */
export function FindingsSort({ sort, order, onSortChange }: FindingsSortProps) {
  const current = OPTIONS.find((option) => option.value === sort) ?? OPTIONS[0]
  const Icon = order === 'asc' ? ArrowUp : ArrowDown

  return (
    <div className="flex items-center gap-2">
      <Select
        value={sort}
        onValueChange={(next: FindingSort | null) => {
          if (next) {
            onSortChange(nextSort({ sort, order }, next, defaultFindingOrder))
          }
        }}
      >
        <SelectTrigger aria-label="Sort findings by" className="h-8 w-36">
          <SelectValue items={ITEMS} />
        </SelectTrigger>
        <SelectContent>
          {OPTIONS.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Button
        size="sm"
        variant="outline"
        aria-label={`${current.orders[order]}, reverse the order`}
        onClick={() => {
          onSortChange(nextSort({ sort, order }, sort, defaultFindingOrder))
        }}
      >
        <Icon aria-hidden="true" />
        {current.orders[order]}
      </Button>
    </div>
  )
}
