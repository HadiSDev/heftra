import { queryOptions } from '@tanstack/react-query'
import type { ApiClient } from './api-client'
import type { EntrySummaryRow, Report } from './types'

/** Ledger totals per entry type (`GET /reports/entries-summary`), in the company's own currency. */
export function entriesSummaryOptions(api: ApiClient) {
  return queryOptions({
    queryKey: ['reports', 'entries-summary', { currency_mode: 'base' }],
    queryFn: () =>
      api.get<Report<EntrySummaryRow>>('/api/v1/reports/entries-summary', {
        currency_mode: 'base',
      }),
  })
}
