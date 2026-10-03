import { FileText } from 'lucide-react'
import { Button, Card, Skeleton } from '#/components/ui'
import { sortAgreements } from '#/lib/agreements/list-sort'
import type { AgreementSort } from '#/lib/agreements/list-sort'
import type { AgreementSummaryRead } from '#/lib/api/agreement-types'
import type { SortOrder } from '#/lib/api/types'
import { AgreementUpload } from './agreement-upload'
import type { AgreementUploadProps } from './agreement-upload'
import { AgreementsTable } from './agreements-table'

export interface AgreementsPanelProps {
  agreements: Array<AgreementSummaryRead> | undefined
  error: boolean
  onRetry: () => void
  sort: AgreementSort
  order: SortOrder
  onSort: (column: AgreementSort) => void
  /** Upload controls, for managers only. */
  upload: AgreementUploadProps | null
}

/** Agreements: the list with its rule breaks, and the upload for managers. */
export function AgreementsPanel({
  agreements,
  error,
  onRetry,
  sort,
  order,
  onSort,
  upload,
}: AgreementsPanelProps) {
  const openBreaks = (agreements ?? []).reduce(
    (total, agreement) => total + agreement.open_rule_breaks,
    0,
  )
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-tight">
          Agreements
        </h1>
        <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
          Trade and framework agreements with your suppliers, and where spend
          breaks them.
          {openBreaks > 0 ? (
            <span className="font-medium text-destructive">
              {' '}
              {openBreaks} rule {openBreaks === 1 ? 'break is' : 'breaks are'}{' '}
              open.
            </span>
          ) : null}
        </p>
      </div>
      {upload ? <AgreementUpload {...upload} /> : null}
      <Card role="region" aria-label="Agreements list" className="p-2">
        {error ? (
          <div className="flex items-center justify-between gap-4 p-4">
            <p className="text-sm text-destructive">
              The agreements could not be loaded.
            </p>
            <Button variant="outline" size="sm" onClick={onRetry}>
              Try again
            </Button>
          </div>
        ) : null}
        {!error && agreements === undefined ? (
          <div
            className="flex flex-col gap-2 p-4"
            aria-label="Loading agreements"
          >
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : null}
        {agreements && agreements.length === 0 ? (
          <div className="flex flex-col items-center gap-2 p-10 text-center">
            <FileText
              className="size-8 text-muted-foreground"
              aria-hidden="true"
            />
            <p className="text-sm text-muted-foreground">
              No agreements yet.
              {upload
                ? ' Upload one above to check your spend against it.'
                : ''}
            </p>
          </div>
        ) : null}
        {agreements && agreements.length > 0 ? (
          <AgreementsTable
            agreements={sortAgreements(agreements, { sort, order })}
            sort={sort}
            order={order}
            onSort={onSort}
          />
        ) : null}
      </Card>
    </div>
  )
}
