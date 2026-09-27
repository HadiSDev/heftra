import { queryOptions } from '@tanstack/react-query'
import type { QueryClient, UseMutationOptions } from '@tanstack/react-query'
import type { ApiClient } from './api-client'
import { entriesKey } from './entries'
import type {
  EmissionFactorsStatusRead,
  FactorSetActivationRead,
  ReferenceImportKind,
  ReferenceImportRead,
} from './admin-emission-factor-types'

const BASE = '/api/v1/admin/emission-factors'

/** How often the jobs are refetched while one is unfinished. */
export const IMPORT_POLL_INTERVAL_MS = 2000

/** How many recent jobs the page lists. */
const RECENT_IMPORT_LIMIT = 20

/** Key prefix for everything on the Emission factors admin page. */
export const adminEmissionFactorsKey = ['admin', 'emission-factors'] as const

/** Whether a job has yet to finish. */
export function isImportUnfinished(job: ReferenceImportRead): boolean {
  return job.status === 'queued' || job.status === 'running'
}

/** Whether a job of `kind` is queued or running. */
export function hasUnfinishedImport(
  jobs: Array<ReferenceImportRead> | undefined,
  kind: ReferenceImportKind,
): boolean {
  return (jobs ?? []).some(
    (job) => job.kind === kind && isImportUnfinished(job),
  )
}

/** The factor sets, price indices and coverage (`GET /admin/emission-factors`). */
export function emissionFactorsStatusQueryOptions(api: ApiClient) {
  return queryOptions({
    queryKey: [...adminEmissionFactorsKey, 'status'],
    queryFn: () => api.get<EmissionFactorsStatusRead>(BASE),
  })
}

/** The recent import jobs, polled while one is unfinished (`GET /admin/emission-factors/imports`). */
export function referenceImportsQueryOptions(api: ApiClient) {
  return queryOptions({
    queryKey: [...adminEmissionFactorsKey, 'imports'],
    queryFn: () =>
      api.get<Array<ReferenceImportRead>>(`${BASE}/imports`, {
        limit: RECENT_IMPORT_LIMIT,
      }),
    refetchInterval: (query) =>
      (query.state.data ?? []).some(isImportUnfinished)
        ? IMPORT_POLL_INTERVAL_MS
        : false,
  })
}

/** Refresh the admin page, and every figure an activation or new index changes. */
export function invalidateEmissionFigures(queryClient: QueryClient) {
  return Promise.all([
    queryClient.invalidateQueries({ queryKey: adminEmissionFactorsKey }),
    queryClient.invalidateQueries({ queryKey: entriesKey }),
    queryClient.invalidateQueries({ queryKey: ['reports'] }),
    queryClient.invalidateQueries({ queryKey: ['emission-sectors'] }),
  ])
}

/** Make a factor set the one every estimate uses. */
export function activateFactorSetMutation(
  api: ApiClient,
  queryClient: QueryClient,
): UseMutationOptions<FactorSetActivationRead, Error, string> {
  return {
    mutationFn: (factorSetId) =>
      api.post<FactorSetActivationRead>(`${BASE}/sets/${factorSetId}/activate`),
    onSuccess: () => invalidateEmissionFigures(queryClient),
  }
}

/** Start a refresh of a price index from FRED. */
export function refreshPriceIndexMutation(
  api: ApiClient,
  queryClient: QueryClient,
): UseMutationOptions<ReferenceImportRead, Error, string> {
  return {
    mutationFn: (series) =>
      api.post<ReferenceImportRead>(`${BASE}/price-index/refresh`, { series }),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: [...adminEmissionFactorsKey, 'imports'],
      }),
  }
}

export interface WorkbookUpload {
  file: File
  activate: boolean
  onProgress?: (sent: number) => void
}

/** Upload an Open CEDA workbook to be imported in the background. */
export function uploadWorkbookMutation(
  api: ApiClient,
  queryClient: QueryClient,
): UseMutationOptions<ReferenceImportRead, Error, WorkbookUpload> {
  return {
    mutationFn: ({ file, activate, onProgress }) => {
      const form = new FormData()
      form.append('file', file)
      form.append('activate', String(activate))
      return api.upload<ReferenceImportRead>(
        `${BASE}/workbooks`,
        form,
        onProgress,
      )
    },
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: [...adminEmissionFactorsKey, 'imports'],
      }),
  }
}
