import type * as React from 'react'
import { PiggyBank } from 'lucide-react'
import { Button, Card, Pagination, Skeleton } from '#/components/ui'
import type {
  AlternativeFilters,
  AlternativeSort,
  AlternativesPage,
  ItemSummary,
} from '#/lib/api/alternative-types'
import type { CompanyRead, SortOrder } from '#/lib/api/types'
import { isFiltered } from '#/lib/alternative-search'
import { formatCount, formatMoney } from '#/lib/format/format'
import { AlternativesTable } from './alternatives-table'
import { AlternativesToolbar } from './alternatives-toolbar'

function Headline({ result }: { result: AlternativesPage }) {
  return (
    <Card className="flex flex-wrap items-center gap-5 p-6">
      <span className="flex size-12 shrink-0 items-center justify-center rounded-full bg-success/15 text-success">
        <PiggyBank className="size-6" aria-hidden="true" />
      </span>
      <div className="flex min-w-0 flex-col gap-0.5">
        <span className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
          Possible yearly saving
        </span>
        <span className="font-display text-3xl font-semibold tracking-tight text-success tabular-nums">
          {result.total_saving !== null
            ? formatMoney(result.total_saving, result.currency)
            : 'Across currencies'}
        </span>
        <span className="text-sm text-muted-foreground">
          The best alternative of each of {formatCount(result.total)}{' '}
          {result.total === 1 ? 'item' : 'items'}, at last year’s quantities
        </span>
      </div>
    </Card>
  )
}

function Message({
  title,
  children,
  action,
}: {
  title: string
  children: React.ReactNode
  action?: React.ReactNode
}) {
  return (
    <Card className="p-8 text-center">
      <h2 className="font-display text-base font-medium">{title}</h2>
      <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
        {children}
      </p>
      {action ? <div className="mt-4">{action}</div> : null}
    </Card>
  )
}

function Empty({
  result,
  filtered,
  onClear,
}: {
  result: AlternativesPage
  filtered: boolean
  onClear: () => void
}) {
  if (filtered) {
    return (
      <Message
        title="Nothing cheaper matches"
        action={
          <Button variant="outline" onClick={onClear}>
            Clear filters
          </Button>
        }
      >
        No open alternative passes these filters.
      </Message>
    )
  }
  if (result.searched_items === 0) {
    return (
      <Message title="Nothing searched yet">
        Ask for cheaper alternatives from a spend line, or turn on the
        background scan, which searches your largest spend first.
      </Message>
    )
  }
  return (
    <Message title="Nothing cheaper found">
      {formatCount(result.searched_items)}{' '}
      {result.searched_items === 1 ? 'item was' : 'items were'} searched, and no
      open alternative is cheaper.
    </Message>
  )
}

export interface AlternativesPanelProps {
  result: AlternativesPage | undefined
  loading: boolean
  error: boolean
  filters: AlternativeFilters
  sort: AlternativeSort
  order: SortOrder
  /** Whether unit prices can be sorted; false when they would compare currencies. */
  unitPriceSortable: boolean
  companies: Array<CompanyRead>
  onFiltersChange: (changes: Partial<AlternativeFilters>) => void
  onClearFilters: () => void
  onSort: (column: AlternativeSort) => void
  onPageChange: (page: number) => void
  onSelect: (item: ItemSummary) => void
}

/** The Alternatives page body: the possible saving, filters, the items and their states. */
export function AlternativesPanel({
  result,
  loading,
  error,
  filters,
  sort,
  order,
  unitPriceSortable,
  companies,
  onFiltersChange,
  onClearFilters,
  onSort,
  onPageChange,
  onSelect,
}: AlternativesPanelProps) {
  function body() {
    if (error) {
      return (
        <Message title="Couldn’t load the alternatives">
          The request to the web API failed. Check that it is running and
          reachable, then reload.
        </Message>
      )
    }
    if (loading || !result) {
      return (
        <div data-testid="alternatives-loading" className="flex flex-col gap-3">
          <Skeleton className="h-24 rounded-xl" />
          {Array.from({ length: 6 }).map((_, index) => (
            <Skeleton key={index} className="h-16 rounded-md" />
          ))}
        </div>
      )
    }
    if (result.items.length === 0) {
      return (
        <Empty
          result={result}
          filtered={isFiltered(filters)}
          onClear={onClearFilters}
        />
      )
    }
    const pageCount = Math.max(1, Math.ceil(result.total / result.page_size))
    return (
      <>
        <Headline result={result} />
        <AlternativesTable
          items={result.items}
          sort={sort}
          order={order}
          unitPriceSortable={unitPriceSortable}
          onSort={onSort}
          onSelect={onSelect}
        />
        {pageCount > 1 ? (
          <div className="flex justify-end">
            <Pagination
              page={result.page}
              pageCount={pageCount}
              onPageChange={onPageChange}
            />
          </div>
        ) : null}
      </>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <AlternativesToolbar
        filters={filters}
        companies={companies}
        onChange={onFiltersChange}
      />
      {body()}
    </div>
  )
}
