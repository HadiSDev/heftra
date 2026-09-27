import { Button, Card, Skeleton } from '#/components/ui'
import type {
  AdminFactorSetRead,
  EmissionFactorsStatusRead,
  ReferenceImportRead,
} from '#/lib/api/admin-emission-factor-types'
import { CoverageCard } from './coverage-card'
import type { MatchRequest } from './coverage-card'
import { FactorSetsCard } from './factor-sets-card'
import { ImportJobs } from './import-jobs'
import { PriceIndexCard } from './price-index-card'
import { WorkbookUpload } from './workbook-upload'

export interface EmissionFactorsAdminProps {
  status: EmissionFactorsStatusRead | undefined
  statusError: boolean
  onRetry: () => void
  jobs: Array<ReferenceImportRead>
  refreshing: boolean
  refreshError: string | null
  importingWorkbook: boolean
  matchRequests: Record<string, MatchRequest | undefined>
  onActivate: (set: AdminFactorSetRead) => void
  onRefresh: (series: string) => void
  onUpload: (
    file: File,
    activate: boolean,
    onProgress: (sent: number) => void,
  ) => Promise<void>
  onMatch: (companyId: string) => void
}

/** The Emission factors admin page: sets, inflation, upload, imports and coverage. */
export function EmissionFactorsAdmin({
  status,
  statusError,
  onRetry,
  jobs,
  refreshing,
  refreshError,
  importingWorkbook,
  matchRequests,
  onActivate,
  onRefresh,
  onUpload,
  onMatch,
}: EmissionFactorsAdminProps) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="font-display text-lg font-medium">Emission factors</h2>
        <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
          The factor sets and price index every company&apos;s emissions are
          estimated with. Changes here apply to all organizations.
        </p>
      </div>
      {statusError ? (
        <Card className="flex items-center justify-between gap-4 p-6">
          <p className="text-sm text-destructive">
            The emission factors could not be loaded.
          </p>
          <Button variant="outline" size="sm" onClick={onRetry}>
            Try again
          </Button>
        </Card>
      ) : null}
      {!status && !statusError ? (
        <div
          className="flex flex-col gap-6"
          aria-label="Loading emission factors"
        >
          <Skeleton className="h-56 w-full rounded-2xl" />
          <Skeleton className="h-48 w-full rounded-2xl" />
        </div>
      ) : null}
      {status ? (
        <>
          <FactorSetsCard sets={status.sets} onActivate={onActivate} />
          <div className="grid gap-6 lg:grid-cols-2">
            <PriceIndexCard
              indices={status.price_indices}
              refreshing={refreshing}
              error={refreshError}
              onRefresh={onRefresh}
            />
            <WorkbookUpload importing={importingWorkbook} onUpload={onUpload} />
          </div>
        </>
      ) : null}
      <ImportJobs jobs={jobs} />
      {status ? (
        <CoverageCard
          rows={status.coverage}
          requests={matchRequests}
          onMatch={onMatch}
        />
      ) : null}
    </div>
  )
}
