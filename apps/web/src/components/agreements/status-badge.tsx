import { Badge } from '#/components/ui'
import type { AgreementSummaryRead } from '#/lib/api/agreement-types'
import { agreementStatus } from '#/lib/format/agreements'

/** Reading, needs review, active, expired or couldn't read. */
export function AgreementStatusBadge({
  agreement,
}: {
  agreement: AgreementSummaryRead
}) {
  const { label, variant } = agreementStatus(agreement)
  return <Badge variant={variant}>{label}</Badge>
}
