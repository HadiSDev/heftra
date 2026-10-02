import * as React from 'react'
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Button,
  Card,
  Skeleton,
  Tabs,
  TabsList,
  TabsTab,
} from '#/components/ui'
import { AgreementHeading } from '#/components/agreements/detail/agreement-heading'
import { ReportTab } from '#/components/agreements/report/report-tab'
import { TermsTab } from '#/components/agreements/terms/terms-tab'
import {
  defaultAgreementTab,
  validateAgreementSearch,
} from '#/lib/agreement-search'
import type { AgreementTab, ReportView } from '#/lib/agreement-search'
import { ApiError } from '#/lib/api/api-client'
import {
  addTermMutation,
  agreementQueryOptions,
  agreementReportQueryOptions,
  analyseAgreementsMutation,
  invalidateAgreements,
  isAnalysing,
  deleteAgreementMutation,
  readAgreementAgainMutation,
  reviewFindingMutation,
  updateAgreementMutation,
  updateTermMutation,
} from '#/lib/api/agreements'
import type { FindingReviewStatus } from '#/lib/api/agreement-types'
import { vendorsQueryOptions } from '#/lib/api/vendors'
import { canManageCompanies, useApi, usePrincipal } from '#/lib/auth/auth'
import { useAnalysisFinished } from '#/lib/use-analysis-finished'
import { useDebouncedValue } from '#/lib/use-debounced-value'

export const Route = createFileRoute('/_authed/agreements/$agreementId')({
  component: AgreementPage,
  staticData: { title: 'Agreement' },
  validateSearch: validateAgreementSearch,
})

const REVIEW_STATUSES: Record<
  ReportView,
  Array<FindingReviewStatus> | undefined
> = {
  open: ['open'],
  reviewed: ['exception', 'not_in_scope'],
  all: undefined,
}

function message(error: unknown, fallback: string): Error {
  return new Error(error instanceof ApiError ? error.detail : fallback)
}

function AgreementPage() {
  const { agreementId } = Route.useParams()
  const search = Route.useSearch()
  const navigate = useNavigate({ from: Route.fullPath })
  const api = useApi()
  const queryClient = useQueryClient()
  const canEdit = canManageCompanies(usePrincipal())
  const [vendorQuery, setVendorQuery] = React.useState('')
  const debouncedVendors = useDebouncedValue(vendorQuery, 250)

  const agreement = useQuery(agreementQueryOptions(api, agreementId))
  const status = agreement.data?.status
  const tab: AgreementTab = search.tab ?? defaultAgreementTab(agreement.data)
  const view: ReportView = search.view ?? 'open'
  const report = useQuery({
    ...agreementReportQueryOptions(api, agreementId, {
      reviewStatus: REVIEW_STATUSES[view],
    }),
    enabled: tab === 'report' && status === 'active',
  })
  const vendors = useQuery({
    ...vendorsQueryOptions(api, { q: debouncedVendors }),
    enabled: tab === 'terms' && canEdit,
  })

  const updateAgreement = useMutation(updateAgreementMutation(api, queryClient))
  const updateTerm = useMutation(updateTermMutation(api, queryClient))
  const addTerm = useMutation(addTermMutation(api, queryClient))
  const readAgain = useMutation(readAgreementAgainMutation(api, queryClient))
  const review = useMutation(reviewFindingMutation(api, queryClient))
  const analyse = useMutation(analyseAgreementsMutation(api, queryClient))
  const remove = useMutation(deleteAgreementMutation(api, queryClient))
  const refresh = React.useCallback(() => {
    void invalidateAgreements(queryClient)
  }, [queryClient])
  useAnalysisFinished(agreement.data, refresh)

  if (agreement.isError) {
    return (
      <Card className="flex items-center justify-between gap-4 p-6">
        <p className="text-sm text-destructive">
          {agreement.error instanceof ApiError && agreement.error.status === 404
            ? 'This agreement doesn’t exist, or isn’t one of yours.'
            : 'The agreement could not be loaded.'}
        </p>
        <Button
          size="sm"
          variant="outline"
          onClick={() => void agreement.refetch()}
        >
          Try again
        </Button>
      </Card>
    )
  }
  if (!agreement.data) {
    return (
      <div className="flex flex-col gap-4" aria-label="Loading the agreement">
        <Skeleton className="h-16 w-1/2" />
        <Skeleton className="h-96 w-full rounded-2xl" />
      </div>
    )
  }
  const current = agreement.data

  return (
    <div className="flex flex-col gap-6">
      <AgreementHeading
        agreement={current}
        canEdit={canEdit}
        onDelete={async () => {
          await remove.mutateAsync(current.id)
          await navigate({ to: '/agreements' })
        }}
        onReadAgain={async () => {
          try {
            await readAgain.mutateAsync(current.id)
          } catch (error) {
            throw message(error, 'Not queued')
          }
          await navigate({ search: { ...search, tab: 'terms' } })
        }}
      />
      <Tabs
        value={tab}
        onValueChange={(next) => {
          void navigate({ search: { ...search, tab: next as AgreementTab } })
        }}
      >
        <TabsList>
          <TabsTab value="report">Report</TabsTab>
          <TabsTab value="terms">Terms</TabsTab>
        </TabsList>
      </Tabs>
      {tab === 'terms' ? (
        <TermsTab
          agreement={current}
          canEdit={canEdit}
          vendors={vendors.data?.items ?? []}
          onVendorSearch={setVendorQuery}
          busyTermId={updateTerm.isPending ? updateTerm.variables.termId : null}
          onSaveHeader={async (patch) => {
            try {
              await updateAgreement.mutateAsync({
                agreementId: current.id,
                patch,
              })
            } catch (error) {
              throw message(error, 'Not saved')
            }
          }}
          onUpdateTerm={async (termId, patch) => {
            try {
              await updateTerm.mutateAsync({ termId, patch })
            } catch (error) {
              throw message(error, 'Not saved')
            }
          }}
          onAddTerm={async (term) => {
            try {
              await addTerm.mutateAsync({ agreementId: current.id, term })
            } catch (error) {
              throw message(error, 'Not added')
            }
          }}
          onReadAgain={() => {
            readAgain.mutate(current.id)
          }}
        />
      ) : (
        <ReportTab
          agreement={current}
          report={report.data}
          error={report.isError}
          onRetry={() => void report.refetch()}
          view={view}
          onViewChange={(next) => {
            void navigate({ search: { ...search, view: next } })
          }}
          canEdit={canEdit}
          analysing={analyse.isPending || isAnalysing(current)}
          onAnalyse={(full) => {
            analyse.mutate({ companyId: current.company_id, full })
          }}
          onReview={async (findingId, findingReview) => {
            try {
              await review.mutateAsync({ findingId, review: findingReview })
            } catch (error) {
              throw message(error, 'Not saved')
            }
          }}
        />
      )}
    </div>
  )
}
