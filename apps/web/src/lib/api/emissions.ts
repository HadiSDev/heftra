import { keepPreviousData, queryOptions } from '@tanstack/react-query'
import type { ApiClient } from './api-client'
import { entriesKey } from './entries'
import type { EmissionSectorRead, EmissionsSummaryRead } from './emission-types'
import type { EntryFilters } from './types'

/** The listed vouchers' estimated emissions (`GET /erp-entries/vouchers/emissions`). */
export function voucherEmissionsQueryOptions(
  api: ApiClient,
  filters: EntryFilters = {},
) {
  const {
    voucher: _voucher,
    entry: _entry,
    tab: _tab,
    page: _page,
    ...listFilters
  } = filters
  return queryOptions({
    queryKey: [...entriesKey, 'emissions', listFilters],
    queryFn: () =>
      api.get<EmissionsSummaryRead>(
        '/api/v1/erp-entries/vouchers/emissions',
        listFilters,
      ),
    placeholderData: keepPreviousData,
  })
}

/** The active factor set's sectors whose code or name contains `query` (`GET /emission-sectors`). */
export function emissionSectorsQueryOptions(api: ApiClient, query: string) {
  const q = query.trim()
  return queryOptions({
    queryKey: ['emission-sectors', q],
    queryFn: () =>
      api.get<Array<EmissionSectorRead>>('/api/v1/emission-sectors', { q }),
    placeholderData: keepPreviousData,
    staleTime: 5 * 60 * 1000,
  })
}
