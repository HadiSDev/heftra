import * as React from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ActivateDialog } from '#/components/settings/emission-factors/activate-dialog'
import type { MatchRequest } from '#/components/settings/emission-factors/coverage-card'
import { EmissionFactorsAdmin } from '#/components/settings/emission-factors/emission-factors-admin'
import { usePrincipal, useApi } from '#/lib/auth/auth'
import { ApiError } from '#/lib/api/api-client'
import {
  activateFactorSetMutation,
  emissionFactorsStatusQueryOptions,
  hasUnfinishedImport,
  invalidateEmissionFigures,
  refreshPriceIndexMutation,
  referenceImportsQueryOptions,
  uploadWorkbookMutation,
} from '#/lib/api/admin-emission-factors'
import type { AdminFactorSetRead } from '#/lib/api/admin-emission-factor-types'
import { requestRunMutation } from '#/lib/api/pipeline-runs'
import { useImportFinished } from '#/lib/use-import-finished'

export const Route = createFileRoute('/_authed/settings/emission-factors')({
  component: EmissionFactorsRoute,
  staticData: { title: 'Emission factors' },
})

function errorText(error: Error | null): string | null {
  if (!error) {
    return null
  }
  return error instanceof ApiError ? error.detail : error.message
}

function EmissionFactorsRoute() {
  const principal = usePrincipal()
  if (!principal.isSystemAdmin) {
    return <ReadOnlyEmissionFactorsPage />
  }
  return <EmissionFactorsPage />
}

function ReadOnlyEmissionFactorsPage() {
  const api = useApi()
  const status = useQuery(emissionFactorsStatusQueryOptions(api))
  return (
    <EmissionFactorsAdmin
      status={status.data}
      statusError={status.isError}
      onRetry={() => {
        void status.refetch()
      }}
      management={null}
    />
  )
}

function EmissionFactorsPage() {
  const api = useApi()
  const queryClient = useQueryClient()
  const status = useQuery(emissionFactorsStatusQueryOptions(api))
  const jobs = useQuery(referenceImportsQueryOptions(api))
  const activate = useMutation(activateFactorSetMutation(api, queryClient))
  const refresh = useMutation(refreshPriceIndexMutation(api, queryClient))
  const upload = useMutation(uploadWorkbookMutation(api, queryClient))
  const requestRun = useMutation(requestRunMutation(api, queryClient))
  const [target, setTarget] = React.useState<AdminFactorSetRead | null>(null)
  const [matchRequests, setMatchRequests] = React.useState<
    Record<string, MatchRequest | undefined>
  >({})

  const onImportFinished = React.useCallback(() => {
    void invalidateEmissionFigures(queryClient)
  }, [queryClient])
  useImportFinished(jobs.data, onImportFinished)

  const current = status.data?.sets.find((set) => set.active) ?? null

  function closeDialog() {
    setTarget(null)
    activate.reset()
  }

  function onMatch(companyId: string) {
    setMatchRequests((requests) => ({
      ...requests,
      [companyId]: { state: 'pending' },
    }))
    requestRun.mutate(
      { companyId, kind: 'match_emissions' },
      {
        onSuccess: () => {
          setMatchRequests((requests) => ({
            ...requests,
            [companyId]: { state: 'requested' },
          }))
        },
        onError: (error) => {
          setMatchRequests((requests) => ({
            ...requests,
            [companyId]: {
              state: 'failed',
              message: errorText(error) ?? 'Could not request matching',
            },
          }))
        },
      },
    )
  }

  return (
    <>
      <EmissionFactorsAdmin
        status={status.data}
        statusError={status.isError}
        onRetry={() => {
          void status.refetch()
        }}
        management={{
          jobs: jobs.data ?? [],
          refreshing:
            refresh.isPending || hasUnfinishedImport(jobs.data, 'price_index'),
          refreshError: errorText(refresh.error),
          importingWorkbook: hasUnfinishedImport(jobs.data, 'factor_workbook'),
          matchRequests,
          onActivate: setTarget,
          onRefresh: (series) => {
            refresh.mutate(series)
          },
          onUpload: async (file, activateWhenImported, onProgress) => {
            try {
              await upload.mutateAsync({
                file,
                activate: activateWhenImported,
                onProgress,
              })
            } catch (error) {
              throw new Error(
                errorText(error instanceof Error ? error : null) ??
                  'Upload failed',
              )
            }
          },
          onMatch,
        }}
      />
      <ActivateDialog
        target={target}
        current={current}
        busy={activate.isPending}
        error={errorText(activate.error)}
        onClose={closeDialog}
        onConfirm={() => {
          if (target) {
            activate.mutate(target.id, { onSuccess: closeDialog })
          }
        }}
      />
    </>
  )
}
