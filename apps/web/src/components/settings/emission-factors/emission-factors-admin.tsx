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

/** A system admin's controls: activation, refresh, upload, imports and matching. */
export interface EmissionFactorsManagement {
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

export interface EmissionFactorsAdminProps {
  status: EmissionFactorsStatusRead | undefined
  statusError: boolean
  onRetry: () => void
  /** Null renders the page read-only, for anyone but a system admin. */
  management: EmissionFactorsManagement | null
}

/** The Emission factors page: sets, inflation, upload, imports and coverage. */
export function EmissionFactorsAdmin({
  status,
  statusError,
  onRetry,
  management,
}: EmissionFactorsAdminProps) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="font-display text-lg font-medium">Emission factors</h2>
        <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
          The factor sets and price index every company&apos;s emissions are
          estimated with.{' '}
          {management
            ? 'Changes here apply to all organizations.'
            : 'They are shared by every organization, and system admins manage them.'}
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
          <FactorSetsCard
            sets={status.sets}
            onActivate={management?.onActivate}
          />
          <div className="grid gap-6 lg:grid-cols-2">
            <PriceIndexCard
              indices={status.price_indices}
              refreshing={management?.refreshing}
              error={management?.refreshError}
              onRefresh={management?.onRefresh}
            />
            {management ? (
              <WorkbookUpload
                importing={management.importingWorkbook}
                onUpload={management.onUpload}
              />
            ) : null}
          </div>
        </>
      ) : null}
      {management ? <ImportJobs jobs={management.jobs} /> : null}
      {status ? (
        <CoverageCard
          rows={status.coverage}
          requests={management?.matchRequests}
          onMatch={management?.onMatch}
        />
      ) : null}
    </div>
  )
}
