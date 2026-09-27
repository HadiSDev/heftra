import { Link } from '@tanstack/react-router'
import { AlertTriangle } from 'lucide-react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '#/components/ui'
import type { AgreementSummaryRead } from '#/lib/api/agreement-types'
import { formatDay, formatMoney } from '#/lib/format/format'
import { AgreementStatusBadge } from '../status-badge'

function validity(agreement: AgreementSummaryRead): string {
  if (!agreement.starts_on) {
    return 'Dates not set'
  }
  const end = agreement.ends_on ? formatDay(agreement.ends_on) : 'open-ended'
  return `${formatDay(agreement.starts_on)} – ${end}`
}

function RuleBreaks({ agreement }: { agreement: AgreementSummaryRead }) {
  if (agreement.status !== 'active') {
    return <span className="text-muted-foreground">—</span>
  }
  if (agreement.open_rule_breaks === 0) {
    return <span className="text-success">None open</span>
  }
  return (
    <span className="inline-flex items-center gap-1.5 font-medium text-destructive">
      <AlertTriangle className="size-4" aria-hidden="true" />
      {agreement.open_rule_breaks} ·{' '}
      {formatMoney(agreement.rule_break_amount, agreement.base_currency)}
    </span>
  )
}

/** The agreements, newest first, with their state and open rule breaks. */
export function AgreementsTable({
  agreements,
}: {
  agreements: Array<AgreementSummaryRead>
}) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Agreement</TableHead>
          <TableHead>Supplier</TableHead>
          <TableHead>Valid</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="text-right">Open rule breaks</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {agreements.map((agreement) => (
          <TableRow key={agreement.id}>
            <TableCell>
              <Link
                to="/agreements/$agreementId"
                params={{ agreementId: agreement.id }}
                className="font-medium text-foreground hover:underline"
              >
                {agreement.title}
              </Link>
              {agreement.reference ? (
                <div className="text-xs text-muted-foreground">
                  {agreement.reference}
                </div>
              ) : null}
            </TableCell>
            <TableCell>
              {agreement.supplier?.name ?? agreement.supplier_name ?? (
                <span className="text-muted-foreground">Not linked</span>
              )}
            </TableCell>
            <TableCell className="whitespace-nowrap">
              {validity(agreement)}
            </TableCell>
            <TableCell>
              <AgreementStatusBadge agreement={agreement} />
            </TableCell>
            <TableCell className="text-right whitespace-nowrap tabular-nums">
              <RuleBreaks agreement={agreement} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
