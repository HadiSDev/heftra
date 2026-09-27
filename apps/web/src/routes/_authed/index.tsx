import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { DashboardView } from '#/components/dashboard/dashboard-view'
import { useApi } from '#/lib/auth/auth'
import { companiesQueryOptions } from '#/lib/api/companies'
import {
  spendBreakdownOptions,
  spendEmissionsOptions,
  spendInsightsOptions,
  spendOverviewOptions,
  spendTrendOptions,
} from '#/lib/api/spend-reports'
import {
  resolvePeriod,
  spendScope,
  validateDashboardSearch,
} from '#/lib/dashboard-search'

export const Route = createFileRoute('/_authed/')({
  component: DashboardPage,
  staticData: { title: 'Dashboard' },
  validateSearch: validateDashboardSearch,
})

function DashboardPage() {
  const api = useApi()
  const navigate = useNavigate({ from: Route.fullPath })
  const search = Route.useSearch()
  const scope = spendScope(search)

  const companies = useQuery(companiesQueryOptions(api))
  const overview = useQuery(spendOverviewOptions(api, scope))
  const trend = useQuery(spendTrendOptions(api, scope))
  const breakdown = useQuery(spendBreakdownOptions(api, scope))
  const insights = useQuery(spendInsightsOptions(api, scope))
  const emissions = useQuery(spendEmissionsOptions(api, scope))

  return (
    <DashboardView
      search={search}
      resolved={resolvePeriod(search)}
      companies={companies.data ?? []}
      overview={{ data: overview.data, error: overview.isError }}
      trend={{ data: trend.data, error: trend.isError }}
      breakdown={{ data: breakdown.data, error: breakdown.isError }}
      insights={{ data: insights.data, error: insights.isError }}
      emissions={{ data: emissions.data, error: emissions.isError }}
      onSearchChange={(next) => {
        void navigate({ search: next })
      }}
    />
  )
}
