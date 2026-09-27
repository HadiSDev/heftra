import { Card } from '#/components/ui'
import { Metric } from '#/components/entries/summary/metric'
import type { AgreementReport, FindingKind } from '#/lib/api/agreement-types'
import { shareOf } from '#/lib/format/agreements'
import { formatMoney, toNumber } from '#/lib/format/format'

function total(report: AgreementReport, kinds: Array<FindingKind>) {
  return report.totals
    .filter((row) => kinds.includes(row.kind))
    .reduce(
      (sum, row) => ({
        count: sum.count + row.count,
        amount: sum.amount + toNumber(row.amount),
      }),
      { count: 0, amount: 0 },
    )
}

/** In-scope spend, open rule breaks and what else the analysis found, at a glance. */
export function ReportFigures({ report }: { report: AgreementReport }) {
  const currency = report.currency
  const breaks = total(report, ['off_contract', 'overcharge'])
  const overcharges = total(report, ['overcharge'])
  const discounts = total(report, ['missed_discount'])
  const savings = total(report, ['potential_saving'])
  const share = shareOf(report.supplier_spend, report.in_scope_spend)
  return (
    <Card className="grid divide-y divide-border p-0 sm:grid-cols-2 sm:divide-y-0 lg:grid-cols-4 lg:divide-x">
      <Metric
        caption="Open rule breaks"
        value={
          <span className={breaks.count > 0 ? 'text-destructive' : undefined}>
            {breaks.count}
          </span>
        }
      >
        {breaks.count > 0
          ? `${formatMoney(breaks.amount, currency)} bought against the agreement`
          : 'Nothing bought against the agreement'}
      </Metric>
      <Metric
        caption="Spend in scope"
        value={formatMoney(report.in_scope_spend, currency)}
      >
        {share === null
          ? 'No spend in scope yet'
          : `${share}% with the supplier`}
      </Metric>
      <Metric
        caption="Overcharges and missed discounts"
        value={formatMoney(overcharges.amount + discounts.amount, currency)}
      >
        {overcharges.count} overcharged, {discounts.count} without the discount
      </Metric>
      <Metric
        caption="Potential savings"
        value={formatMoney(savings.amount, currency)}
      >
        The agreed terms applied to {savings.count}{' '}
        {savings.count === 1 ? 'purchase' : 'purchases'} elsewhere
      </Metric>
    </Card>
  )
}
