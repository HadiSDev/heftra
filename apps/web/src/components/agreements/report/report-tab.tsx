import { RefreshCw } from 'lucide-react'
import {
  Button,
  Card,
  Skeleton,
  Tabs,
  TabsList,
  TabsTab,
} from '#/components/ui'
import type {
  AgreementRead,
  AgreementReport,
  FindingReview,
} from '#/lib/api/agreement-types'
import type { ReportView } from '#/lib/agreement-search'
import { AnalysisStatus, CoverageNotes } from './analysis-status'
import { Commitments } from './commitments'
import { FindingsList } from './findings-list'
import { ReportFigures } from './report-figures'

export interface ReportTabProps {
  agreement: AgreementRead
  report: AgreementReport | undefined
  error: boolean
  onRetry: () => void
  view: ReportView
  onViewChange: (view: ReportView) => void
  canEdit: boolean
  analysing: boolean
  /** `true` rechecks every line, not only what changed. */
  onAnalyse: (full: boolean) => void
  onReview: (findingId: string, review: FindingReview) => Promise<void>
}

const VIEWS: Array<{ value: ReportView; label: string }> = [
  { value: 'open', label: 'Open' },
  { value: 'reviewed', label: 'Reviewed' },
  { value: 'all', label: 'Everything' },
]

/** What the spend shows against the agreement, rule breaks first. */
export function ReportTab({
  agreement,
  report,
  error,
  onRetry,
  view,
  onViewChange,
  canEdit,
  analysing,
  onAnalyse,
  onReview,
}: ReportTabProps) {
  if (agreement.status !== 'active') {
    return (
      <Card className="p-6 text-sm text-muted-foreground">
        The report starts once the agreement has a supplier, a start date and at
        least one confirmed term.
      </Card>
    )
  }
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-col gap-1">
          <AnalysisStatus agreement={agreement} />
          <CoverageNotes agreement={agreement} />
        </div>
        {canEdit ? (
          <div className="flex flex-wrap items-center gap-2">
            <Button
              size="sm"
              variant="ghost"
              disabled={analysing}
              onClick={() => {
                onAnalyse(true)
              }}
            >
              Check everything again
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={analysing}
              onClick={() => {
                onAnalyse(false)
              }}
            >
              <RefreshCw className={analysing ? 'animate-spin' : undefined} />
              {analysing ? 'Checking…' : 'Check again'}
            </Button>
          </div>
        ) : null}
      </div>
      {error ? (
        <Card className="flex items-center justify-between gap-4 p-5">
          <p className="text-sm text-destructive">
            The report could not be loaded.
          </p>
          <Button size="sm" variant="outline" onClick={onRetry}>
            Try again
          </Button>
        </Card>
      ) : null}
      {!error && !report ? (
        <div className="flex flex-col gap-4" aria-label="Loading the report">
          <Skeleton className="h-28 w-full rounded-2xl" />
          <Skeleton className="h-64 w-full rounded-2xl" />
        </div>
      ) : null}
      {report ? (
        <>
          <ReportFigures report={report} />
          <Commitments
            commitments={report.commitments}
            currency={report.currency}
          />
          <Card
            role="region"
            aria-label="Findings"
            className="flex flex-col gap-3 p-2"
          >
            <div className="flex flex-wrap items-center justify-between gap-2 px-3 pt-3">
              <h2 className="font-display text-base font-medium">
                Findings{' '}
                <span className="text-sm font-normal text-muted-foreground">
                  rule breaks first
                </span>
              </h2>
              <Tabs
                value={view}
                onValueChange={(next) => {
                  onViewChange(next as ReportView)
                }}
              >
                <TabsList>
                  {VIEWS.map((item) => (
                    <TabsTab key={item.value} value={item.value}>
                      {item.label}
                    </TabsTab>
                  ))}
                </TabsList>
              </Tabs>
            </div>
            {report.findings.items.length === 0 ? (
              <p className="p-6 text-center text-sm text-muted-foreground">
                {view === 'open'
                  ? 'Nothing open. Spend in scope follows the agreement.'
                  : 'No findings here.'}
              </p>
            ) : (
              <FindingsList
                findings={report.findings.items}
                companyId={agreement.company_id}
                canReview={canEdit}
                onReview={onReview}
              />
            )}
          </Card>
        </>
      ) : null}
    </div>
  )
}
