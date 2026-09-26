import { Link } from '@tanstack/react-router'
import { formatDay, formatMoney } from '#/lib/format/format'
import type {
  SpendInsightsRow,
  SupplierInsight,
  UncategorizedInsight,
} from '#/lib/api/spend-report-types'
import { ChangeBadge } from '../change-badge'

function Heading({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
      {children}
    </h3>
  )
}

function SupplierItem({
  insight,
  currency,
  detail,
}: {
  insight: SupplierInsight
  currency: string
  detail?: React.ReactNode
}) {
  return (
    <li className="flex items-baseline justify-between gap-3 text-sm">
      <Link
        to="/suppliers/$vendorId"
        params={{ vendorId: insight.id }}
        className="min-w-0 truncate font-medium hover:underline"
        title={insight.name}
      >
        {insight.name}
      </Link>
      <span className="flex shrink-0 items-baseline gap-2">
        <span className="font-mono tabular-nums">
          {formatMoney(insight.amount, currency)}
        </span>
        {detail}
      </span>
    </li>
  )
}

function UncategorizedItem({
  insight,
  currency,
}: {
  insight: UncategorizedInsight
  currency: string
}) {
  const search = insight.voucher_id
    ? { voucher: insight.voucher_id }
    : { entry: insight.entry_id ?? undefined }
  return (
    <li className="flex items-baseline justify-between gap-3 text-sm">
      <Link
        to="/invoice-lines"
        search={search}
        className="min-w-0 truncate hover:underline"
      >
        <span className="font-medium">
          {insight.supplier_name ?? 'No supplier'}
        </span>
        <span className="text-muted-foreground">
          {' '}
          · {formatDay(insight.spent_on)}
        </span>
      </Link>
      <span className="shrink-0 font-mono tabular-nums">
        {formatMoney(insight.amount, currency)}
      </span>
    </li>
  )
}

function Group({
  title,
  children,
  count,
}: {
  title: string
  children: React.ReactNode
  count: number
}) {
  if (count === 0) {
    return null
  }
  return (
    <section aria-label={title} className="flex min-w-0 flex-col gap-2">
      <Heading>{title}</Heading>
      <ul className="flex flex-col gap-1.5">{children}</ul>
    </section>
  )
}

/** One currency's insights, leaving out the lists with nothing in them. */
function CurrencyInsights({
  row,
  showCurrency,
}: {
  row: SpendInsightsRow
  showCurrency: boolean
}) {
  return (
    <div className="flex flex-col gap-4">
      {showCurrency ? <Heading>{row.currency}</Heading> : null}
      <div className="grid gap-5 sm:grid-cols-2">
        <Group title="New suppliers" count={row.new_suppliers.length}>
          {row.new_suppliers.map((insight) => (
            <SupplierItem
              key={insight.id}
              insight={insight}
              currency={row.currency}
            />
          ))}
        </Group>
        <Group title="Biggest increases" count={row.increases.length}>
          {row.increases.map((insight) => (
            <SupplierItem
              key={insight.id}
              insight={insight}
              currency={row.currency}
              detail={
                <ChangeBadge
                  now={insight.amount}
                  before={insight.comparison_amount ?? 0}
                />
              }
            />
          ))}
        </Group>
        <Group title="Recurring spend" count={row.recurring.length}>
          {row.recurring.map((insight) => (
            <SupplierItem
              key={insight.id}
              insight={insight}
              currency={row.currency}
              detail={
                <span className="text-xs text-muted-foreground">a month</span>
              }
            />
          ))}
        </Group>
        <Group title="Largest uncategorized" count={row.uncategorized.length}>
          {row.uncategorized.map((insight) => (
            <UncategorizedItem
              key={insight.voucher_id ?? insight.entry_id ?? insight.spent_on}
              insight={insight}
              currency={row.currency}
            />
          ))}
        </Group>
      </div>
    </div>
  )
}

/** Changes worth a look, per currency; says so when there are none. */
export function InsightLists({ rows }: { rows: Array<SpendInsightsRow> }) {
  const any = rows.some(
    (row) =>
      row.new_suppliers.length +
        row.increases.length +
        row.recurring.length +
        row.uncategorized.length >
      0,
  )
  if (!any) {
    return (
      <p className="text-sm text-muted-foreground">
        Nothing stands out in this period.
      </p>
    )
  }
  return (
    <div className="flex flex-col gap-6">
      {rows.map((row) => (
        <CurrencyInsights
          key={row.currency}
          row={row}
          showCurrency={rows.length > 1}
        />
      ))}
    </div>
  )
}
