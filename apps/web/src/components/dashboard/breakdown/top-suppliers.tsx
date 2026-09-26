import { Link } from '@tanstack/react-router'
import { CountryFlag } from '#/components/fields/country-flag'
import { formatMoney, toNumber } from '#/lib/format/format'
import type { SpendBreakdownRow } from '#/lib/api/spend-report-types'
import { ChangeBadge } from '../change-badge'
import { formatShare } from '../change'

/** The suppliers with the most spend in the period, each opening its page. */
export function TopSuppliers({ rows }: { rows: Array<SpendBreakdownRow> }) {
  return (
    <div className="flex flex-col gap-6">
      {rows.map((row) => {
        const total = toNumber(row.spend)
        return (
          <section
            key={row.currency}
            aria-label={`Top suppliers in ${row.currency}`}
            className="flex flex-col gap-2"
          >
            {rows.length > 1 ? (
              <h3 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                {row.currency}
              </h3>
            ) : null}
            {row.suppliers.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No supplier had spend in the period.
              </p>
            ) : (
              <ol className="flex flex-col divide-y divide-border">
                {row.suppliers.map((supplier) => (
                  <li
                    key={supplier.id}
                    className="flex items-center gap-3 py-2 text-sm"
                  >
                    {supplier.country_code ? (
                      <CountryFlag country={supplier.country_code} />
                    ) : (
                      <span aria-hidden="true" className="size-5 shrink-0" />
                    )}
                    <Link
                      to="/suppliers/$vendorId"
                      params={{ vendorId: supplier.id }}
                      className="min-w-0 flex-1 truncate font-medium hover:underline"
                      title={supplier.name}
                    >
                      {supplier.name}
                    </Link>
                    <span className="font-mono tabular-nums">
                      {formatMoney(supplier.spend, row.currency)}
                    </span>
                    <span className="w-9 text-right text-xs text-muted-foreground tabular-nums">
                      {formatShare(
                        total > 0 ? toNumber(supplier.spend) / total : 0,
                      )}
                    </span>
                    <ChangeBadge
                      now={supplier.spend}
                      before={supplier.comparison_spend}
                      className="w-12 justify-end"
                    />
                  </li>
                ))}
              </ol>
            )}
          </section>
        )
      })}
    </div>
  )
}
