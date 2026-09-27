import { Link } from '@tanstack/react-router'
import { Progress } from '#/components/ui'
import { formatEmissions } from '#/lib/format/emissions'
import { toNumber } from '#/lib/format/format'
import type { EmissionsSpendRow } from '#/lib/api/emission-types'
import type { SpendEmissions } from '#/lib/api/spend-report-types'
import { describePeriod } from '#/lib/dashboard-search'
import { ChangeBadge } from '../change-badge'
import { formatShare } from '../change'
import { Sparkline } from '../tiles/sparkline'
import { EmissionsMethod } from '#/components/entries/emissions/emissions-method'

export interface EmissionsLinkSearch {
  from: string
  to: string
  company_id?: string
}

function estimatedShare(row: EmissionsSpendRow): number | null {
  const posted = toNumber(row.posted_spend)
  return posted > 0 ? toNumber(row.estimated_spend) / posted : null
}

function ShareEstimated({ rows }: { rows: Array<EmissionsSpendRow> }) {
  return (
    <ul className="flex flex-col gap-2">
      {rows.map((row) => {
        const share = estimatedShare(row)
        return (
          <li key={row.currency} className="flex flex-col gap-1">
            <span className="text-xs text-muted-foreground">
              {share === null
                ? `No ${row.currency} spend posted`
                : `${formatShare(share)} of ${row.currency} spend estimated`}
            </span>
            {share === null ? null : (
              <Progress
                aria-label={`Share of ${row.currency} spend estimated`}
                value={Math.min(100, Math.round(share * 100))}
              />
            )}
          </li>
        )
      })}
    </ul>
  )
}

function TopSectors({ report }: { report: SpendEmissions }) {
  if (report.top_sectors.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No line in the period has an emission sector yet.
      </p>
    )
  }
  const largest = toNumber(report.top_sectors[0].kg_co2e) || 1
  return (
    <ol
      aria-label="Sectors with the most emissions"
      className="flex flex-col gap-2.5"
    >
      {report.top_sectors.map((sector) => (
        <li key={sector.code} className="flex flex-col gap-1">
          <span className="flex items-baseline justify-between gap-3 text-sm">
            <span className="min-w-0 truncate">{sector.name}</span>
            <span className="shrink-0 font-mono text-xs tabular-nums text-muted-foreground">
              {formatEmissions(sector.kg_co2e)}
            </span>
          </span>
          <span
            aria-hidden="true"
            className="h-1.5 rounded-full bg-chart-1"
            style={{ width: `${(toNumber(sector.kg_co2e) / largest) * 100}%` }}
          />
        </li>
      ))}
    </ol>
  )
}

/** The period's estimated emissions, their change, twelve months and the top sectors. */
export function EmissionsFigures({
  report,
  linkSearch,
}: {
  report: SpendEmissions
  linkSearch: EmissionsLinkSearch
}) {
  const factorSet = report.factor_set
  if (factorSet === null || report.kg_co2e === null) {
    return (
      <p className="text-sm text-muted-foreground">
        No emission factors are imported, so no emissions are estimated yet.
      </p>
    )
  }
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div className="flex min-w-0 flex-col gap-3">
        <div className="flex flex-wrap items-baseline gap-x-2">
          <span className="font-display text-2xl font-semibold tracking-tight tabular-nums">
            {formatEmissions(report.kg_co2e)}
          </span>
          <ChangeBadge
            now={report.kg_co2e}
            before={report.comparison_kg_co2e ?? 0}
          />
        </div>
        <span className="text-xs text-muted-foreground">
          vs {describePeriod(report.comparison)}
        </span>
        <Sparkline
          months={report.months.map((month) => ({
            month: month.month,
            amount: month.kg_co2e,
          }))}
        />
        <ShareEstimated rows={report.spend} />
        <p className="text-xs text-muted-foreground">
          <EmissionsMethod factorSet={factorSet} /> · {factorSet.attribution}
        </p>
        <Link
          to="/invoice-lines"
          search={linkSearch}
          className="text-xs font-medium text-primary hover:underline"
        >
          See the vouchers in Spend Lines
        </Link>
      </div>
      <TopSectors report={report} />
    </div>
  )
}
