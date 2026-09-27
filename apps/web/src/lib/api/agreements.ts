import { queryOptions } from '@tanstack/react-query'
import type { QueryClient, UseMutationOptions } from '@tanstack/react-query'
import type { ApiClient } from './api-client'
import type {
  AgreementPatch,
  AgreementRead,
  AgreementReport,
  AgreementSummaryRead,
  FindingKind,
  FindingRead,
  FindingReview,
  FindingReviewStatus,
  TermCreate,
  TermPatch,
  TermRead,
} from './agreement-types'
import type { PipelineRunRead } from './types'

/** How often a reading agreement or an unfinished analysis is checked on. */
export const AGREEMENT_POLL_INTERVAL_MS = 3000

/** Key prefix for every agreement query. */
export const agreementsKey = ['agreements'] as const

function isReading(status: AgreementSummaryRead['status']): boolean {
  return status === 'pending' || status === 'reading'
}

/** The chosen company's agreements, or every active company's (`GET /agreements`). */
export function agreementsQueryOptions(api: ApiClient, companyId?: string) {
  return queryOptions({
    queryKey: [...agreementsKey, 'list', companyId ?? null],
    queryFn: () =>
      api.get<Array<AgreementSummaryRead>>('/api/v1/agreements', {
        company_id: companyId,
      }),
    refetchInterval: (query) =>
      (query.state.data ?? []).some((row) => isReading(row.status))
        ? AGREEMENT_POLL_INTERVAL_MS
        : false,
  })
}

/** One agreement with its terms (`GET /agreements/{id}`). */
export function agreementQueryOptions(api: ApiClient, agreementId: string) {
  return queryOptions({
    queryKey: [...agreementsKey, 'detail', agreementId],
    queryFn: () => api.get<AgreementRead>(`/api/v1/agreements/${agreementId}`),
    refetchInterval: (query) =>
      query.state.data && isReading(query.state.data.status)
        ? AGREEMENT_POLL_INTERVAL_MS
        : false,
  })
}

export interface ReportFilters {
  kind?: Array<FindingKind>
  reviewStatus?: Array<FindingReviewStatus>
  page?: number
}

/** An agreement's report (`GET /agreements/{id}/report`). */
export function agreementReportQueryOptions(
  api: ApiClient,
  agreementId: string,
  filters: ReportFilters = {},
) {
  const params = new URLSearchParams()
  for (const kind of filters.kind ?? []) {
    params.append('kind', kind)
  }
  for (const status of filters.reviewStatus ?? []) {
    params.append('review_status', status)
  }
  params.set('page', String(filters.page ?? 1))
  return queryOptions({
    queryKey: [...agreementsKey, 'report', agreementId, filters],
    queryFn: () =>
      api.get<AgreementReport>(
        `/api/v1/agreements/${agreementId}/report?${params.toString()}`,
      ),
  })
}

/** The agreement's PDF (`GET /agreements/{id}/document`). */
export function agreementDocumentQueryOptions(
  api: ApiClient,
  agreementId: string,
) {
  return queryOptions({
    queryKey: [...agreementsKey, 'document', agreementId],
    queryFn: () => api.getBlob(`/api/v1/agreements/${agreementId}/document`),
    staleTime: Infinity,
    retry: false,
  })
}

function invalidateAgreements(queryClient: QueryClient) {
  return Promise.all([
    queryClient.invalidateQueries({ queryKey: agreementsKey }),
    queryClient.invalidateQueries({
      queryKey: ['reports', 'agreement-compliance'],
    }),
  ])
}

export interface AgreementUpload {
  companyId: string
  file: File
  onProgress?: (sent: number) => void
}

/** Upload an agreement PDF for a company. */
export function uploadAgreementMutation(
  api: ApiClient,
  queryClient: QueryClient,
): UseMutationOptions<AgreementRead, Error, AgreementUpload> {
  return {
    mutationFn: ({ companyId, file, onProgress }) => {
      const form = new FormData()
      form.append('file', file)
      return api.upload<AgreementRead>(
        `/api/v1/companies/${companyId}/agreements`,
        form,
        onProgress,
      )
    },
    onSuccess: () => invalidateAgreements(queryClient),
  }
}

/** Correct an agreement's supplier, title, reference, dates or currency. */
export function updateAgreementMutation(
  api: ApiClient,
  queryClient: QueryClient,
): UseMutationOptions<
  AgreementRead,
  Error,
  { agreementId: string; patch: AgreementPatch }
> {
  return {
    mutationFn: ({ agreementId, patch }) =>
      api.patch<AgreementRead>(`/api/v1/agreements/${agreementId}`, patch),
    onSuccess: () => invalidateAgreements(queryClient),
  }
}

/** Queue the agreement's document to be read again. */
export function readAgreementAgainMutation(
  api: ApiClient,
  queryClient: QueryClient,
): UseMutationOptions<AgreementRead, Error, string> {
  return {
    mutationFn: (agreementId) =>
      api.post<AgreementRead>(`/api/v1/agreements/${agreementId}/read`),
    onSuccess: () => invalidateAgreements(queryClient),
  }
}

/** Delete an agreement, its terms, findings and file. */
export function deleteAgreementMutation(
  api: ApiClient,
  queryClient: QueryClient,
): UseMutationOptions<void, Error, string> {
  return {
    mutationFn: (agreementId) =>
      api.del<void>(`/api/v1/agreements/${agreementId}`),
    onSuccess: () => invalidateAgreements(queryClient),
  }
}

/** Add a term the reader missed. */
export function addTermMutation(
  api: ApiClient,
  queryClient: QueryClient,
): UseMutationOptions<
  TermRead,
  Error,
  { agreementId: string; term: TermCreate }
> {
  return {
    mutationFn: ({ agreementId, term }) =>
      api.post<TermRead>(`/api/v1/agreements/${agreementId}/terms`, term),
    onSuccess: () => invalidateAgreements(queryClient),
  }
}

/** Edit, confirm or reject a term. */
export function updateTermMutation(
  api: ApiClient,
  queryClient: QueryClient,
): UseMutationOptions<TermRead, Error, { termId: string; patch: TermPatch }> {
  return {
    mutationFn: ({ termId, patch }) =>
      api.patch<TermRead>(`/api/v1/agreement-terms/${termId}`, patch),
    onSuccess: () => invalidateAgreements(queryClient),
  }
}

/** Accept a finding as an exception, rule it out of scope, or reopen it. */
export function reviewFindingMutation(
  api: ApiClient,
  queryClient: QueryClient,
): UseMutationOptions<
  FindingRead,
  Error,
  { findingId: string; review: FindingReview }
> {
  return {
    mutationFn: ({ findingId, review }) =>
      api.patch<FindingRead>(`/api/v1/agreement-findings/${findingId}`, review),
    onSuccess: () => invalidateAgreements(queryClient),
  }
}

/** Ask for the company's spend to be checked against its agreements again. */
export function analyseAgreementsMutation(
  api: ApiClient,
  queryClient: QueryClient,
): UseMutationOptions<PipelineRunRead, Error, string> {
  return {
    mutationFn: (companyId) =>
      api.post<PipelineRunRead>(
        `/api/v1/companies/${companyId}/agreements/analyse`,
      ),
    onSuccess: () => invalidateAgreements(queryClient),
  }
}
