import { ChevronRight } from 'lucide-react'
import {
  Badge,
  SortHeader,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '#/components/ui'
import type { AlternativeSort, ItemSummary } from '#/lib/api/alternative-types'
import type { SortOrder } from '#/lib/api/types'
import {
  CLASS_LABELS,
  MATCH_LABELS,
  MATCH_VARIANTS,
  SOURCE_LABELS,
  perUnit,
} from '#/lib/format/alternatives'
import { formatCount, formatMoney } from '#/lib/format/format'

function BestAlternative({ item }: { item: ItemSummary }) {
  if (!item.best) {
    return <span className="text-muted-foreground">—</span>
  }
  return (
    <div className="flex flex-col gap-1">
      <span className="flex flex-wrap items-center gap-1.5">
        <Badge variant={MATCH_VARIANTS[item.best.match]}>
          {MATCH_LABELS[item.best.match]}
        </Badge>
        <span className="text-xs text-muted-foreground">
          {SOURCE_LABELS[item.best.source]}
        </span>
      </span>
      <span className="tabular-nums">
        {perUnit(item.best.unit_price, item.best.currency, item.pricing_unit)}
      </span>
    </div>
  )
}

export interface AlternativesTableProps {
  items: Array<ItemSummary>
  sort: AlternativeSort
  order: SortOrder
  /** Whether unit prices can be sorted; false when they would compare currencies. */
  unitPriceSortable: boolean
  onSort: (column: AlternativeSort) => void
  onSelect: (item: ItemSummary) => void
}

/** Items with their best alternative, in the chosen order; a row opens the item. */
export function AlternativesTable({
  items,
  sort,
  order,
  unitPriceSortable,
  onSort,
  onSelect,
}: AlternativesTableProps) {
  const header = { sort, order, onSort }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <SortHeader label="Item" column="name" {...header} />
          <SortHeader label="Supplier" column="supplier" {...header} />
          <SortHeader
            label="Now"
            column="unit_price"
            align="right"
            sortable={unitPriceSortable}
            {...header}
          />
          <TableHead>Best alternative</TableHead>
          <SortHeader
            label="Alternatives"
            column="alternatives"
            align="right"
            {...header}
          />
          <SortHeader
            label="Yearly saving"
            column="saving"
            align="right"
            {...header}
          />
          <TableHead>
            <span className="sr-only">Open</span>
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((item) => (
          <TableRow
            key={item.id}
            className="cursor-pointer"
            onClick={() => {
              onSelect(item)
            }}
          >
            <TableCell className="max-w-72">
              <div className="flex min-w-0 flex-col gap-0.5">
                <button
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation()
                    onSelect(item)
                  }}
                  className="truncate text-left font-medium outline-none hover:underline focus-visible:ring-2 focus-visible:ring-ring"
                >
                  {item.name}
                </button>
                {item.item_class ? (
                  <span className="text-xs text-muted-foreground">
                    {CLASS_LABELS[item.item_class]}
                  </span>
                ) : null}
              </div>
            </TableCell>
            <TableCell className="text-muted-foreground">
              {item.supplier_name ?? '—'}
            </TableCell>
            <TableCell className="text-right whitespace-nowrap tabular-nums">
              {perUnit(item.unit_price, item.currency, item.pricing_unit)}
            </TableCell>
            <TableCell>
              <BestAlternative item={item} />
            </TableCell>
            <TableCell className="text-right tabular-nums">
              {formatCount(item.alternatives)}
            </TableCell>
            <TableCell className="text-right whitespace-nowrap">
              <span className="font-display text-lg font-semibold text-success tabular-nums">
                {item.best?.saving_yearly != null
                  ? formatMoney(item.best.saving_yearly, item.best.currency)
                  : '—'}
              </span>
            </TableCell>
            <TableCell className="w-8 pl-0">
              <ChevronRight
                className="size-4 text-muted-foreground"
                aria-hidden="true"
              />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
