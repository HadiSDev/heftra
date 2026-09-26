import { Link } from '@tanstack/react-router'
import { CircleCheck, TriangleAlert } from 'lucide-react'
import { formatCount } from '#/lib/format/format'
import type { AttentionCounts } from '#/lib/api/spend-report-types'
import type { EntryFilters } from '#/lib/api/types'
import { Tile } from './tile'

interface AttentionItem {
  count: number
  one: string
  many: string
  search: EntryFilters
}

function items(attention: AttentionCounts): Array<AttentionItem> {
  const all: Array<AttentionItem> = [
    {
      count: attention.needs_review_lines,
      one: 'line to review',
      many: 'lines to review',
      search: { needs_review: true },
    },
    {
      count: attention.failed_documents,
      one: 'document failed',
      many: 'documents failed',
      search: { document: 'failed' },
    },
    {
      count: attention.totals_mismatch,
      one: 'total disagrees',
      many: 'totals disagree',
      search: { document: 'mismatch' },
    },
  ]
  return all.filter((item) => item.count > 0)
}

/** Work waiting now, each count opening the vouchers it counts. */
export function AttentionTile({ attention }: { attention: AttentionCounts }) {
  const waiting = items(attention)
  return (
    <Tile caption="Needs attention" icon={<TriangleAlert />}>
      {waiting.length === 0 ? (
        <p className="flex items-center gap-2 text-sm font-medium text-success">
          <CircleCheck aria-hidden="true" className="size-4" />
          All clear
        </p>
      ) : (
        <ul className="flex flex-col gap-1.5">
          {waiting.map((item) => (
            <li key={item.one}>
              <Link
                to="/invoice-lines"
                search={item.search}
                className="inline-flex items-baseline gap-1.5 text-sm hover:underline"
              >
                <span className="font-display text-lg font-semibold tabular-nums">
                  {formatCount(item.count)}
                </span>{' '}
                <span className="text-muted-foreground">
                  {item.count === 1 ? item.one : item.many}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Tile>
  )
}
