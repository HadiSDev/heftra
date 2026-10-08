import { Link } from '@tanstack/react-router'
import { Loader2, PiggyBank, Search } from 'lucide-react'
import { Button } from '#/components/ui'
import type { ItemRead } from '#/lib/api/alternative-types'
import { formatMoney, toNumber } from '#/lib/format/format'

export interface LineAlternativesViewProps {
  /** The line's item; null when it hasn't been looked at, undefined while loading. */
  item: ItemRead | null | undefined
  canManage: boolean
  /** Whether this is the hosted demo, which hides actions it can't serve. */
  demo?: boolean
  pending: boolean
  error: string | null
  onFind: () => void
}

function bestSaving(item: ItemRead): number | null {
  const savings = item.alternatives
    .filter(
      (entry) => entry.review_status === 'open' && entry.saving_yearly !== null,
    )
    .map((entry) => toNumber(entry.saving_yearly ?? 0))
  return savings.length > 0 ? Math.max(...savings) : null
}

function Body({
  item,
  canManage,
  demo = false,
  pending,
  onFind,
}: LineAlternativesViewProps) {
  if (item === undefined) {
    return <p className="text-sm text-muted-foreground">Loading…</p>
  }
  if (item?.searching || pending) {
    return (
      <p role="status" className="flex items-center gap-2 text-sm">
        <Loader2
          className="size-4 animate-spin text-primary"
          aria-hidden="true"
        />
        Searching for cheaper alternatives…
      </p>
    )
  }
  const open = item
    ? item.alternatives.filter((entry) => entry.review_status === 'open')
    : []
  const best = item ? bestSaving(item) : null
  if (item && open.length > 0) {
    return (
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm">
          {best !== null ? (
            <>
              Up to{' '}
              <span className="font-semibold text-success">
                {formatMoney(best, item.currency)}
              </span>{' '}
              a year with{' '}
            </>
          ) : null}
          {open.length} {open.length === 1 ? 'alternative' : 'alternatives'}
        </p>
        <Link
          to="/alternatives/$itemId"
          params={{ itemId: item.id }}
          className="text-sm font-medium hover:underline"
        >
          See the alternatives
        </Link>
      </div>
    )
  }
  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <p className="text-sm text-muted-foreground">
        {item?.searched_at
          ? 'Nothing cheaper and at least as good was found.'
          : 'Not searched for cheaper alternatives yet.'}
      </p>
      {canManage && !demo ? (
        <Button size="sm" variant="outline" onClick={onFind}>
          <Search />
          Find cheaper alternatives
        </Button>
      ) : null}
    </div>
  )
}

/** Under a spend line: what its item could cost elsewhere, or a way to find out. */
export function LineAlternativesView(props: LineAlternativesViewProps) {
  return (
    <section
      aria-label="Cheaper alternatives"
      className="mt-4 flex flex-col gap-2 rounded-lg border border-border p-4"
    >
      <h3 className="flex items-center gap-2 text-sm font-medium">
        <PiggyBank className="size-4 text-success" aria-hidden="true" />
        Cheaper alternatives
      </h3>
      <Body {...props} />
      {props.error ? (
        <p className="text-sm text-destructive">{props.error}</p>
      ) : null}
    </section>
  )
}
