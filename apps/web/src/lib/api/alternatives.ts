import { keepPreviousData, queryOptions } from '@tanstack/react-query'
import type { QueryClient, UseMutationOptions } from '@tanstack/react-query'
import type { ApiClient } from './api-client'
import type {
  AlternativeFilters,
  AlternativeRead,
  AlternativeReview,
  AlternativesPage,
  ItemLineRead,
  ItemRead,
  Specification,
} from './alternative-types'
import type { PipelineRunRead } from './types'

/** How often an item being searched is checked on. */
export const SEARCH_POLL_INTERVAL_MS = 3000

/** Key prefix for every alternatives and item query. */
export const alternativesKey = ['alternatives'] as const

function invalidateAlternatives(queryClient: QueryClient) {
  return queryClient.invalidateQueries({ queryKey: alternativesKey })
}

/** Items with an open alternative, best saving first unless sorted (`GET /alternatives`). */
export function alternativesQueryOptions(
  api: ApiClient,
  filters: AlternativeFilters,
) {
  return queryOptions({
    queryKey: [...alternativesKey, 'list', filters],
    queryFn: () =>
      api.get<AlternativesPage>('/api/v1/alternatives', {
        company_id: filters.company_id,
        source: filters.source,
        match: filters.match,
        item_class: filters.item_class,
        sort: filters.sort,
        order: filters.order,
        page: filters.page,
      }),
    placeholderData: keepPreviousData,
  })
}

/** One item with its specification and alternatives (`GET /items/{id}`). */
export function itemQueryOptions(api: ApiClient, itemId: string) {
  return queryOptions({
    queryKey: [...alternativesKey, 'item', itemId],
    queryFn: () => api.get<ItemRead>(`/api/v1/items/${itemId}`),
    refetchInterval: (query) =>
      query.state.data?.searching ? SEARCH_POLL_INTERVAL_MS : false,
  })
}

/** The spend lines an item was bought on in the last 12 months (`GET /items/{id}/lines`). */
export function itemLinesQueryOptions(api: ApiClient, itemId: string) {
  return queryOptions({
    queryKey: [...alternativesKey, 'item', itemId, 'lines'],
    queryFn: () =>
      api.get<Array<ItemLineRead>>(`/api/v1/items/${itemId}/lines`),
  })
}

/** The item a spend line bought, once stored (`GET /invoice-lines/{id}/item`). */
export function lineItemQueryOptions(api: ApiClient, lineId: string) {
  return queryOptions({
    queryKey: [...alternativesKey, 'line', lineId],
    queryFn: () => api.get<ItemRead>(`/api/v1/invoice-lines/${lineId}/item`),
    retry: false,
    refetchInterval: (query) =>
      query.state.data?.searching ? SEARCH_POLL_INTERVAL_MS : false,
  })
}

/** Correct an item's specification (`PATCH /items/{id}/specification`). */
export function updateSpecificationMutation(
  api: ApiClient,
  queryClient: QueryClient,
): UseMutationOptions<
  ItemRead,
  Error,
  { itemId: string; spec: Specification }
> {
  return {
    mutationFn: ({ itemId, spec }) =>
      api.patch<ItemRead>(`/api/v1/items/${itemId}/specification`, spec),
    onSuccess: () => invalidateAlternatives(queryClient),
  }
}

/** Queue a search of an item's alternatives (`POST /items/{id}/find-alternatives`). */
export function findAlternativesMutation(
  api: ApiClient,
  queryClient: QueryClient,
): UseMutationOptions<PipelineRunRead, Error, string> {
  return {
    mutationFn: (itemId) =>
      api.post<PipelineRunRead>(`/api/v1/items/${itemId}/find-alternatives`),
    onSuccess: () => invalidateAlternatives(queryClient),
  }
}

/** Queue a search for a spend line's item (`POST /invoice-lines/{id}/find-alternatives`). */
export function findLineAlternativesMutation(
  api: ApiClient,
  queryClient: QueryClient,
): UseMutationOptions<ItemRead, Error, string> {
  return {
    mutationFn: (lineId) =>
      api.post<ItemRead>(`/api/v1/invoice-lines/${lineId}/find-alternatives`),
    onSuccess: () => invalidateAlternatives(queryClient),
  }
}

/** Dismiss, mark switched or reopen an alternative (`PATCH /alternatives/{id}`). */
export function reviewAlternativeMutation(
  api: ApiClient,
  queryClient: QueryClient,
): UseMutationOptions<
  AlternativeRead,
  Error,
  { alternativeId: string; review: AlternativeReview }
> {
  return {
    mutationFn: ({ alternativeId, review }) =>
      api.patch<AlternativeRead>(
        `/api/v1/alternatives/${alternativeId}`,
        review,
      ),
    onSuccess: () => invalidateAlternatives(queryClient),
  }
}
