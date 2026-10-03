import * as React from 'react'
import { Link } from '@tanstack/react-router'
import { ChevronRight } from 'lucide-react'
import {
  Card,
  Skeleton,
  SortHeader,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '#/components/ui'
import type { ItemLineRead } from '#/lib/api/alternative-types'
import {
  DEFAULT_ITEM_LINE_SORT,
  itemLineOrder,
  sortItemLines,
} from '#/lib/alternatives/item-lines'
import type { ItemLineSort } from '#/lib/alternatives/item-lines'
import {
  formatCount,
  formatDay,
  formatMoney,
  toNumber,
} from '#/lib/format/format'
import { nextSort } from '#/lib/sorting'

/** The element id the header's line count scrolls to. */
export const ITEM_LINES_ID = 'spend-lines'

function lineDetail(line: ItemLineRead): string {
  const quantity =
    line.quantity === null
      ? null
      : [formatCount(toNumber(line.quantity)), line.unit]
          .filter(Boolean)
          .join(' ')
  return (
    [line.invoice_number ? `Invoice ${line.invoice_number}` : null, quantity]
      .filter(Boolean)
      .join(' · ') || '—'
  )
}

function LineRow({
  line,
  companyId,
}: {
  line: ItemLineRead
  companyId: string
}) {
  return (
    <TableRow>
      <TableCell>
        <p className="font-medium">{formatDay(line.invoice_date)}</p>
        <p className="text-xs text-muted-foreground">{lineDetail(line)}</p>
      </TableCell>
      <TableCell className="text-right font-medium tabular-nums">
        {line.base_amount !== null
          ? formatMoney(line.base_amount, line.base_currency)
          : '—'}
      </TableCell>
      <TableCell className="text-right">
        {line.voucher_id ? (
          <Link
            to="/invoice-lines"
            search={{
              company_id: companyId,
              voucher: line.voucher_id,
              tab: 'lines',
            }}
            className="group inline-flex items-center gap-1 text-xs font-medium whitespace-nowrap text-primary hover:underline"
            aria-label={`Open the voucher of the line bought ${formatDay(line.invoice_date)}`}
          >
            Open
            <ChevronRight
              className="size-4 transition-transform group-hover:translate-x-0.5"
              aria-hidden="true"
            />
          </Link>
        ) : (
          <span className="text-xs whitespace-nowrap text-muted-foreground">
            Not posted yet
          </span>
        )}
      </TableCell>
    </TableRow>
  )
}

function LinesTable({
  lines,
  companyId,
}: {
  lines: Array<ItemLineRead>
  companyId: string
}) {
  const [sorting, setSorting] = React.useState(DEFAULT_ITEM_LINE_SORT)
  const header = {
    sort: sorting.sort,
    order: sorting.order,
    onSort: (column: ItemLineSort) => {
      setSorting(nextSort(sorting, column, itemLineOrder))
    },
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <SortHeader label="Date" column="date" {...header} />
          <SortHeader
            label="Amount"
            column="amount"
            align="right"
            {...header}
          />
          <TableHead>
            <span className="sr-only">Voucher</span>
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sortItemLines(lines, sorting).map((line) => (
          <LineRow key={line.id} line={line} companyId={companyId} />
        ))}
      </TableBody>
    </Table>
  )
}

export interface ItemLinesCardProps {
  companyId: string
  /** The item's lines, newest first; undefined while loading, null when they failed to load. */
  lines: Array<ItemLineRead> | undefined | null
}

/** The spend lines behind the item's figures, each opening its voucher in Spend Lines. */
export function ItemLinesCard({ companyId, lines }: ItemLinesCardProps) {
  return (
    <section
      id={ITEM_LINES_ID}
      aria-labelledby={`${ITEM_LINES_ID}-heading`}
      className="flex scroll-mt-6 flex-col gap-3"
    >
      <div className="flex items-baseline justify-between gap-2 px-1">
        <h2
          id={`${ITEM_LINES_ID}-heading`}
          className="font-display text-base font-medium"
        >
          Spend lines
        </h2>
        {lines ? (
          <span className="text-xs text-muted-foreground">
            {formatCount(lines.length)} in the last 12 months
          </span>
        ) : null}
      </div>
      {lines === null ? (
        <Card className="p-5 text-sm text-destructive">
          The lines could not be loaded.
        </Card>
      ) : lines === undefined ? (
        <Card
          className="flex flex-col gap-2 p-5"
          aria-label="Loading the lines"
        >
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </Card>
      ) : lines.length === 0 ? (
        <Card className="p-5 text-sm text-muted-foreground">
          No lines in the last 12 months.
        </Card>
      ) : (
        <LinesTable lines={lines} companyId={companyId} />
      )}
    </section>
  )
}
