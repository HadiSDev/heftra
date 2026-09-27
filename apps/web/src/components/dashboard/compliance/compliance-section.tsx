import { Link } from '@tanstack/react-router'
import { AlertTriangle, ShieldCheck } from 'lucide-react'
import type { AgreementCompliance } from '#/lib/api/agreement-types'
import { formatMoney, toNumber } from '#/lib/format/format'

/** The period's open contract rule breaks and who was bought from off-contract. */
export function ComplianceFigures({ report }: { report: AgreementCompliance }) {
  if (!report.has_active_agreement) {
    return (
      <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-muted-foreground">
        <p>
          No active agreements yet. Upload your framework agreements to see
          where spend breaks them.
        </p>
        <Link
          to="/agreements"
          className="font-medium text-primary hover:underline"
        >
          Go to Agreements
        </Link>
      </div>
    )
  }
  const currency = report.currency
  if (report.open_rule_breaks === 0) {
    return (
      <div className="flex items-center gap-3 text-sm">
        <ShieldCheck className="size-6 text-success" aria-hidden="true" />
        <p>
          No open rule breaks in the period.{' '}
          <Link
            to="/agreements"
            className="font-medium text-primary hover:underline"
          >
            See the agreements
          </Link>
        </p>
      </div>
    )
  }
  const largest = toNumber(report.top_suppliers[0]?.amount ?? 0) || 1
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2 text-destructive">
          <AlertTriangle className="size-5" aria-hidden="true" />
          <span className="font-display text-2xl font-semibold tabular-nums">
            {report.open_rule_breaks}
          </span>
          <span className="text-sm font-medium">
            open rule {report.open_rule_breaks === 1 ? 'break' : 'breaks'}
          </span>
        </div>
        <p className="text-sm text-muted-foreground">
          {formatMoney(report.rule_break_amount, currency)} in all:{' '}
          {formatMoney(report.off_contract_amount, currency)} bought
          off-contract, {formatMoney(report.overcharge_amount, currency)}{' '}
          overcharged.
        </p>
        <Link
          to="/agreements"
          className="text-xs font-medium text-primary hover:underline"
        >
          Review them in Agreements
        </Link>
      </div>
      {report.top_suppliers.length > 0 ? (
        <ol
          aria-label="Bought from off-contract"
          className="flex flex-col gap-2"
        >
          {report.top_suppliers.map((supplier) => (
            <li
              key={supplier.vendor_id ?? supplier.name}
              className="flex flex-col gap-1"
            >
              <div className="flex justify-between gap-3 text-sm">
                <span className="truncate">{supplier.name}</span>
                <span className="shrink-0 tabular-nums">
                  {formatMoney(supplier.amount, currency)}
                </span>
              </div>
              <div className="h-1.5 rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-destructive/70"
                  style={{
                    width: `${Math.max(4, (toNumber(supplier.amount) / largest) * 100)}%`,
                  }}
                />
              </div>
            </li>
          ))}
        </ol>
      ) : null}
    </div>
  )
}
