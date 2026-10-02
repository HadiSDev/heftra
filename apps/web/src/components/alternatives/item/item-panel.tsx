import * as React from 'react'
import { Loader2, Pencil, Search } from 'lucide-react'
import { Button, Card } from '#/components/ui'
import type {
  AlternativeReview,
  ItemLineRead,
  ItemRead,
  Specification,
} from '#/lib/api/alternative-types'
import { PRICE_NOTES, perUnit, unitLabel } from '#/lib/format/alternatives'
import {
  formatCount,
  formatMoney,
  formatRelativeTime,
  toNumber,
} from '#/lib/format/format'
import { AlternativeCard } from './alternative-card'
import { ITEM_LINES_ID, ItemLinesCard } from './item-lines-card'
import { SpecificationCard } from './specification-card'
import { SpecificationForm } from './specification-form'

function SearchStatus({ item }: { item: ItemRead }) {
  if (item.searching) {
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
  return (
    <p role="status" className="text-sm text-muted-foreground">
      {item.searched_at
        ? `Searched ${formatRelativeTime(item.searched_at)}.`
        : 'Not searched yet.'}
    </p>
  )
}

function Header({ item }: { item: ItemRead }) {
  const unit = item.spec?.pricing_unit ?? null
  return (
    <div className="flex flex-col gap-2">
      <h1 className="font-display text-2xl font-semibold tracking-tight">
        {item.spec?.name ?? item.item_name ?? 'Item'}
      </h1>
      <p className="text-sm text-muted-foreground">
        {[item.supplier_name, item.category_path.join(' › '), item.item_name]
          .filter(Boolean)
          .join(' · ')}
      </p>
      <Card className="mt-2 grid divide-y divide-border p-0 sm:grid-cols-3 sm:divide-x sm:divide-y-0">
        <div className="flex flex-col gap-1 px-5 py-4">
          <span className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
            You pay
          </span>
          <span className="font-display text-xl font-semibold tabular-nums">
            {perUnit(item.unit_price, item.currency, unit)}
          </span>
          <span className="text-sm text-muted-foreground">
            {item.price_note ? PRICE_NOTES[item.price_note] : 'Excl. VAT'}
          </span>
        </div>
        <div className="flex flex-col gap-1 px-5 py-4">
          <span className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
            Bought last year
          </span>
          <span className="font-display text-xl font-semibold tabular-nums">
            {item.quantity !== null
              ? `${formatCount(Math.round(toNumber(item.quantity)))} ${unitLabel(unit)}`
              : '—'}
          </span>
          <span className="text-sm text-muted-foreground">
            {formatMoney(item.spend, item.currency)} excl. VAT over{' '}
            <button
              type="button"
              onClick={showLines}
              className="font-medium text-primary hover:underline"
            >
              {formatCount(item.lines)} {item.lines === 1 ? 'line' : 'lines'}
            </button>
          </span>
        </div>
        <div className="flex flex-col gap-1 px-5 py-4">
          <span className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
            Best yearly saving
          </span>
          <span className="font-display text-xl font-semibold text-success tabular-nums">
            {bestSaving(item)}
          </span>
        </div>
      </Card>
    </div>
  )
}

function showLines() {
  document
    .getElementById(ITEM_LINES_ID)
    ?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function bestSaving(item: ItemRead): string {
  const open = item.alternatives.filter(
    (alternative) =>
      alternative.review_status === 'open' &&
      alternative.saving_yearly !== null,
  )
  if (open.length === 0) {
    return '—'
  }
  const best = Math.max(
    ...open.map((entry) => toNumber(entry.saving_yearly ?? 0)),
  )
  return formatMoney(best, item.currency)
}

export interface ItemPanelProps {
  item: ItemRead
  /** The item's spend lines, newest first; undefined while loading, null when they failed. */
  lines: Array<ItemLineRead> | undefined | null
  canManage: boolean
  searchPending: boolean
  onSearch: () => void
  onSaveSpec: (spec: Specification) => Promise<void>
  onReview: (alternativeId: string, review: AlternativeReview) => Promise<void>
}

/** An item: what it costs, its specification, and its alternatives, best saving first. */
export function ItemPanel({
  item,
  lines,
  canManage,
  searchPending,
  onSearch,
  onSaveSpec,
  onReview,
}: ItemPanelProps) {
  const [editing, setEditing] = React.useState(false)
  const unit = item.spec?.pricing_unit ?? null
  return (
    <div className="flex flex-col gap-6">
      <Header item={item} />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <SearchStatus item={item} />
        {canManage ? (
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              disabled={editing}
              onClick={() => {
                setEditing(true)
              }}
            >
              <Pencil />
              Correct the specification
            </Button>
            <Button
              disabled={item.searching || searchPending}
              onClick={onSearch}
            >
              <Search />
              Find cheaper alternatives
            </Button>
          </div>
        ) : null}
      </div>
      <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <section aria-label="Alternatives" className="flex flex-col gap-4">
          {item.alternatives.length === 0 ? (
            <Card className="p-6 text-sm text-muted-foreground">
              {item.searched_at
                ? 'Nothing cheaper and at least as good was found.'
                : 'Search to find cheaper alternatives to this item.'}
            </Card>
          ) : (
            item.alternatives.map((alternative) => (
              <AlternativeCard
                key={alternative.id}
                alternative={alternative}
                pricingUnit={unit}
                canReview={canManage}
                onReview={(review) => onReview(alternative.id, review)}
              />
            ))
          )}
        </section>
        <aside className="flex flex-col gap-4">
          {editing ? (
            <SpecificationForm
              spec={item.spec}
              lineUnit={item.unit}
              onCancel={() => {
                setEditing(false)
              }}
              onSave={async (spec) => {
                await onSaveSpec(spec)
                setEditing(false)
              }}
            />
          ) : (
            <SpecificationCard item={item} />
          )}
          <ItemLinesCard companyId={item.company_id} lines={lines} />
        </aside>
      </div>
    </div>
  )
}
