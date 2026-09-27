import { keepPreviousData, queryOptions } from '@tanstack/react-query'
import type { ApiClient } from './api-client'
import type { AgreementCompliance } from './agreement-types'
import type {
  SpendBreakdown,
  SpendEmissions,
  SpendInsights,
  SpendOverview,
  SpendScope,
  SpendTrend,
} from './spend-report-types'

type SpendReport =
  | 'spend-overview'
  | 'spend-trend'
  | 'spend-breakdown'
  | 'spend-insights'
  | 'spend-emissions'
  | 'agreement-compliance'

function spendReportOptions<T>(
  api: ApiClient,
  report: SpendReport,
  scope: SpendScope,
) {
  return queryOptions({
    queryKey: ['reports', report, scope],
    queryFn: () => api.get<T>(`/api/v1/reports/${report}`, { ...scope }),
    placeholderData: keepPreviousData,
  })
}

/** The tiles' figures (`GET /reports/spend-overview`). */
export function spendOverviewOptions(api: ApiClient, scope: SpendScope) {
  return spendReportOptions<SpendOverview>(api, 'spend-overview', scope)
}

/** Twelve months by the top categories (`GET /reports/spend-trend`). */
export function spendTrendOptions(api: ApiClient, scope: SpendScope) {
  return spendReportOptions<SpendTrend>(api, 'spend-trend', scope)
}

/** Spend by category and the top suppliers (`GET /reports/spend-breakdown`). */
export function spendBreakdownOptions(api: ApiClient, scope: SpendScope) {
  return spendReportOptions<SpendBreakdown>(api, 'spend-breakdown', scope)
}

/** Changes worth a look (`GET /reports/spend-insights`). */
export function spendInsightsOptions(api: ApiClient, scope: SpendScope) {
  return spendReportOptions<SpendInsights>(api, 'spend-insights', scope)
}

/** The period's estimated emissions (`GET /reports/spend-emissions`). */
export function spendEmissionsOptions(api: ApiClient, scope: SpendScope) {
  return spendReportOptions<SpendEmissions>(api, 'spend-emissions', scope)
}

/** The period's open contract rule breaks (`GET /reports/agreement-compliance`). */
export function agreementComplianceOptions(api: ApiClient, scope: SpendScope) {
  return spendReportOptions<AgreementCompliance>(
    api,
    'agreement-compliance',
    scope,
  )
}
