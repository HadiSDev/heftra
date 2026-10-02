import { ChevronRight } from 'lucide-react'
import { Badge } from '#/components/ui'
import type { ItemSummary } from '#/lib/api/alternative-types'
import {
  CLASS_LABELS,
  MATCH_LABELS,
  MATCH_VARIANTS,
  SOURCE_LABELS,
  perUnit,
} from '#/lib/format/alternatives'
import { formatMoney } from '#/lib/format/format'

/** Items with their best alternative, largest yearly saving first; a row opens the item. */
export function AlternativesTable({
  items,
  onSelect,
}: {
  items: Array<ItemSummary>
  onSelect: (item: ItemSummary) => void
}) {
  return (
    <ul className="flex flex-col divide-y divide-border rounded-xl border border-border bg-card">
      {items.map((item) => (
        <li key={item.id}>
          <button
            type="button"
            onClick={() => {
              onSelect(item)
            }}
            className="grid w-full gap-x-6 gap-y-2 px-5 py-4 text-left outline-none transition hover:bg-muted/40 focus-visible:bg-muted/40 sm:grid-cols-[minmax(0,1fr)_auto_auto]"
          >
            <div className="flex min-w-0 flex-col gap-1">
              <span className="truncate font-medium">{item.name}</span>
              <span className="text-xs text-muted-foreground">
                {[
                  item.supplier_name,
                  item.item_class ? CLASS_LABELS[item.item_class] : null,
                  `now ${perUnit(item.unit_price, item.currency, item.pricing_unit)}`,
                ]
                  .filter(Boolean)
                  .join(' · ')}
              </span>
            </div>
            {item.best ? (
              <div className="flex flex-col gap-1 sm:items-end">
                <span className="flex flex-wrap items-center gap-1.5">
                  <Badge variant={MATCH_VARIANTS[item.best.match]}>
                    {MATCH_LABELS[item.best.match]}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {SOURCE_LABELS[item.best.source]}
                  </span>
                </span>
                <span className="text-sm tabular-nums">
                  {perUnit(
                    item.best.unit_price,
                    item.best.currency,
                    item.pricing_unit,
                  )}
                </span>
              </div>
            ) : null}
            <div className="flex items-center gap-3 sm:justify-end">
              <div className="flex flex-col sm:items-end">
                <span className="font-display text-lg font-semibold text-success tabular-nums">
                  {item.best?.saving_yearly != null
                    ? formatMoney(item.best.saving_yearly, item.best.currency)
                    : '—'}
                </span>
                <span className="text-xs text-muted-foreground">
                  a year
                  {item.alternatives > 1
                    ? ` · ${item.alternatives} alternatives`
                    : ''}
                </span>
              </div>
              <ChevronRight
                className="size-4 shrink-0 text-muted-foreground"
                aria-hidden="true"
              />
            </div>
          </button>
        </li>
      ))}
    </ul>
  )
}
