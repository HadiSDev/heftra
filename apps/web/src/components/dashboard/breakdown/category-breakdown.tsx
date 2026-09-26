import * as React from 'react'
import { ChevronRight } from 'lucide-react'
import { cn } from '#/components/ui'
import { formatMoney, toNumber } from '#/lib/format/format'
import type {
  CategorySpendRead,
  SpendBreakdownRow,
} from '#/lib/api/spend-report-types'
import { ChangeBadge } from '../change-badge'
import { formatShare } from '../change'

function categoryName(category: CategorySpendRead, child: boolean): string {
  if (category.name) {
    return category.name
  }
  return child ? 'No subcategory' : 'Not categorized'
}

function ShareBar({ share, muted }: { share: number; muted: boolean }) {
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
      <span
        className={cn(
          'block h-full rounded-full',
          muted ? 'bg-muted-foreground/40' : 'bg-primary',
        )}
        style={{ width: `${Math.max(share * 100, share > 0 ? 1 : 0)}%` }}
      />
    </div>
  )
}

function CategoryRow({
  category,
  total,
  currency,
  child = false,
}: {
  category: CategorySpendRead
  total: number
  currency: string
  child?: boolean
}) {
  const [open, setOpen] = React.useState(false)
  const share = total > 0 ? toNumber(category.spend) / total : 0
  const name = categoryName(category, child)
  const expandable = !child && category.children.length > 0

  const label = (
    <span
      className={cn(
        'min-w-0 truncate text-left',
        child ? 'text-muted-foreground' : 'font-medium',
        category.name === null && !child && 'italic text-muted-foreground',
      )}
      title={name}
    >
      {name}
    </span>
  )

  return (
    <li className="flex flex-col gap-1.5">
      <div className="flex items-baseline justify-between gap-3 text-sm">
        {expandable ? (
          <button
            type="button"
            aria-expanded={open}
            onClick={() => setOpen(!open)}
            className="flex min-w-0 items-center gap-1 outline-none hover:underline focus-visible:ring-2 focus-visible:ring-ring"
          >
            <ChevronRight
              aria-hidden="true"
              className={cn(
                'size-4 shrink-0 transition-transform',
                open && 'rotate-90',
              )}
            />
            {label}
          </button>
        ) : (
          <span className={cn('flex min-w-0 items-center', !child && 'pl-5')}>
            {label}
          </span>
        )}
        <span className="flex shrink-0 items-baseline gap-2">
          <span className="font-mono tabular-nums">
            {formatMoney(category.spend, currency)}
          </span>
          <span className="w-9 text-right text-xs text-muted-foreground tabular-nums">
            {formatShare(share)}
          </span>
          <ChangeBadge
            now={category.spend}
            before={category.comparison_spend}
            className="w-12 justify-end"
          />
        </span>
      </div>
      <div className={cn(child ? 'pl-10' : 'pl-5')}>
        <ShareBar share={share} muted={category.name === null} />
      </div>
      {expandable && open ? (
        <ul className="flex flex-col gap-2 pt-1 pl-5">
          {category.children.map((childCategory) => (
            <CategoryRow
              key={childCategory.name ?? 'none'}
              category={childCategory}
              total={total}
              currency={currency}
              child
            />
          ))}
        </ul>
      ) : null}
    </li>
  )
}

/** Spend by top-level category, each expandable to the level below. */
export function CategoryBreakdown({
  rows,
}: {
  rows: Array<SpendBreakdownRow>
}) {
  return (
    <div className="flex flex-col gap-6">
      {rows.map((row) => (
        <section
          key={row.currency}
          aria-label={`Spend by category in ${row.currency}`}
          className="flex flex-col gap-3"
        >
          {rows.length > 1 ? (
            <h3 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
              {row.currency}
            </h3>
          ) : null}
          <ul className="flex flex-col gap-4">
            {row.categories.map((category) => (
              <CategoryRow
                key={category.name ?? 'none'}
                category={category}
                total={toNumber(row.spend)}
                currency={row.currency}
              />
            ))}
          </ul>
        </section>
      ))}
    </div>
  )
}
