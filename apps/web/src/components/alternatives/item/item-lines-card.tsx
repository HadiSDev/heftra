import { Link } from '@tanstack/react-router'
import { ChevronRight } from 'lucide-react'
import { Card, Skeleton } from '#/components/ui'
import type { ItemLineRead } from '#/lib/api/alternative-types'
import {
  formatCount,
  formatDay,
  formatMoney,
  toNumber,
} from '#/lib/format/format'

/** The element id the header's line count links to. */
export const ITEM_LINES_ID = 'spend-lines'

function lineQuantity(line: ItemLineRead): string | null {
  if (line.quantity === null) {
    return null
  }
  return [formatCount(toNumber(line.quantity)), line.unit]
    .filter(Boolean)
    .join(' ')
}

function LineSummary({ line }: { line: ItemLineRead }) {
  const quantity = lineQuantity(line)
  return (
    <>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium">{formatDay(line.invoice_date)}</p>
        <p className="truncate text-xs text-muted-foreground">
          {[
            line.invoice_number ? `Invoice ${line.invoice_number}` : null,
            quantity,
          ]
            .filter(Boolean)
            .join(' · ') || '—'}
        </p>
      </div>
      <span className="text-sm font-medium tabular-nums">
        {line.base_amount !== null
          ? formatMoney(line.base_amount, line.base_currency)
          : '—'}
      </span>
    </>
  )
}

function LineRow({
  line,
  companyId,
}: {
  line: ItemLineRead
  companyId: string
}) {
  if (!line.voucher_id) {
    return (
      <li className="flex items-center gap-3 px-5 py-3">
        <LineSummary line={line} />
        <span className="w-24 text-right text-xs text-muted-foreground">
          Not posted yet
        </span>
      </li>
    )
  }
  return (
    <li>
      <Link
        to="/invoice-lines"
        search={{
          company_id: companyId,
          voucher: line.voucher_id,
          tab: 'lines',
        }}
        className="group flex items-center gap-3 px-5 py-3 transition-colors hover:bg-muted/60 focus-visible:bg-muted/60 focus-visible:outline-none"
        aria-label={`Open the voucher of the line bought ${formatDay(line.invoice_date)}`}
      >
        <LineSummary line={line} />
        <span className="flex w-24 items-center justify-end gap-1 text-xs font-medium text-primary">
          Open
          <ChevronRight
            className="size-4 transition-transform group-hover:translate-x-0.5"
            aria-hidden="true"
          />
        </span>
      </Link>
    </li>
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
    <Card id={ITEM_LINES_ID} className="scroll-mt-6 overflow-hidden p-0">
      <div className="flex items-baseline justify-between gap-2 border-b border-border px-5 py-4">
        <h2 className="font-display text-base font-medium">Spend lines</h2>
        {lines ? (
          <span className="text-xs text-muted-foreground">
            {formatCount(lines.length)} in the last 12 months
          </span>
        ) : null}
      </div>
      {lines === null ? (
        <p className="px-5 py-4 text-sm text-destructive">
          The lines could not be loaded.
        </p>
      ) : lines === undefined ? (
        <div className="flex flex-col gap-2 p-5" aria-label="Loading the lines">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      ) : lines.length === 0 ? (
        <p className="px-5 py-4 text-sm text-muted-foreground">
          No lines in the last 12 months.
        </p>
      ) : (
        <ul className="divide-y divide-border">
          {lines.map((line) => (
            <LineRow key={line.id} line={line} companyId={companyId} />
          ))}
        </ul>
      )}
    </Card>
  )
}
