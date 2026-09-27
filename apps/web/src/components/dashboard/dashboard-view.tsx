import { BarChart3 } from 'lucide-react'
import { Button, Card } from '#/components/ui'
import { toNumber } from '#/lib/format/format'
import { describePeriod } from '#/lib/dashboard-search'
import type { DashboardSearch } from '#/lib/dashboard-search'
import type {
  SpendBreakdown,
  SpendEmissions,
  SpendInsights,
  SpendOverview,
  SpendTrend,
} from '#/lib/api/spend-report-types'
import type { CompanyRead } from '#/lib/api/types'
import { CategoryBreakdown } from './breakdown/category-breakdown'
import { TopSuppliers } from './breakdown/top-suppliers'
import { DashboardControls } from './controls/dashboard-controls'
import { InsightLists } from './insights/insight-lists'
import { DashboardSection } from './section'
import { EmissionsFigures } from './emissions/emissions-section'
import { OverviewTiles } from './tiles/overview-tiles'
import { TrendChart } from './trend/trend-chart'

/** A report's data and whether it failed. */
export interface ReportState<T> {
  data: T | undefined
  error: boolean
}

export interface DashboardViewProps {
  search: DashboardSearch
  resolved: { from: string; to: string }
  companies: Array<CompanyRead>
  overview: ReportState<SpendOverview>
  trend: ReportState<SpendTrend>
  breakdown: ReportState<SpendBreakdown>
  insights: ReportState<SpendInsights>
  emissions: ReportState<SpendEmissions>
  onSearchChange: (next: DashboardSearch) => void
}

function hasSpend(overview: SpendOverview): boolean {
  return overview.rows.some((row) => toNumber(row.spend) !== 0)
}

function EmptyPeriod({
  offerYear,
  onShowYear,
}: {
  offerYear: boolean
  onShowYear: () => void
}) {
  return (
    <Card className="p-10 text-center">
      <div className="mx-auto grid size-12 place-items-center rounded-xl bg-muted text-muted-foreground">
        <BarChart3 className="size-6" />
      </div>
      <h2 className="mt-4 font-display text-base font-medium">
        No spend in this period
      </h2>
      <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
        Nothing was posted to an expense account in the chosen period.
      </p>
      {offerYear ? (
        <Button variant="outline" className="mt-4" onClick={onShowYear}>
          Show the last 12 months
        </Button>
      ) : null}
    </Card>
  )
}

/** The dashboard: controls, tiles, the trend, the breakdowns and the insights. */
export function DashboardView({
  search,
  resolved,
  companies,
  overview,
  trend,
  breakdown,
  insights,
  emissions,
  onSearchChange,
}: DashboardViewProps) {
  const empty = overview.data !== undefined && !hasSpend(overview.data)
  const comparison = overview.data?.comparison ?? breakdown.data?.comparison

  return (
    <div className="flex flex-col gap-6">
      <DashboardControls
        search={search}
        resolved={resolved}
        companies={companies}
        onChange={onSearchChange}
      />
      {empty ? (
        <EmptyPeriod
          offerYear={search.period !== '12m'}
          onShowYear={() =>
            onSearchChange({
              ...search,
              period: '12m',
              from: undefined,
              to: undefined,
            })
          }
        />
      ) : (
        <>
          <OverviewTiles overview={overview.data} error={overview.error} />
          <DashboardSection
            title="Spend over time"
            description="The last 12 months, by the largest categories"
            loading={trend.data === undefined}
            error={trend.error}
            placeholderClassName="h-80"
          >
            <div className="flex flex-col gap-6">
              {trend.data?.rows.map((row) => (
                <TrendChart
                  key={row.currency}
                  row={row}
                  showCurrency={(trend.data?.rows.length ?? 0) > 1}
                />
              ))}
            </div>
          </DashboardSection>
          <DashboardSection
            title="Emissions"
            description="Estimated from spend; the last 12 months and the largest sectors"
            loading={emissions.data === undefined}
            error={emissions.error}
            placeholderClassName="h-56"
          >
            {emissions.data ? (
              <EmissionsFigures
                report={emissions.data}
                linkSearch={
                  search.company_id
                    ? { ...resolved, company_id: search.company_id }
                    : resolved
                }
              />
            ) : null}
          </DashboardSection>
          <div className="grid items-start gap-6 lg:grid-cols-2">
            <DashboardSection
              title="Spend by category"
              description={
                comparison
                  ? `Change vs ${describePeriod(comparison)}`
                  : undefined
              }
              loading={breakdown.data === undefined}
              error={breakdown.error}
              placeholderClassName="h-72"
            >
              <CategoryBreakdown rows={breakdown.data?.rows ?? []} />
            </DashboardSection>
            <DashboardSection
              title="Top suppliers"
              description={
                comparison
                  ? `Change vs ${describePeriod(comparison)}`
                  : undefined
              }
              loading={breakdown.data === undefined}
              error={breakdown.error}
              placeholderClassName="h-72"
            >
              <TopSuppliers rows={breakdown.data?.rows ?? []} />
            </DashboardSection>
          </div>
          <DashboardSection
            title="Insights"
            loading={insights.data === undefined}
            error={insights.error}
            placeholderClassName="h-48"
          >
            <InsightLists rows={insights.data?.rows ?? []} />
          </DashboardSection>
        </>
      )}
    </div>
  )
}
