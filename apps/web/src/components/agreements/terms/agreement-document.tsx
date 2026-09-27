import { useQuery } from '@tanstack/react-query'
import { DocumentPane } from '#/components/entries/invoice-document/invoice-document'
import type { PageRequest } from '#/components/entries/invoice-document/invoice-document'
import { agreementDocumentQueryOptions } from '#/lib/api/agreements'
import { useApi } from '#/lib/auth/auth'

/** The agreement's PDF, scrolled to a quoted page on request. */
export function AgreementDocument({
  agreementId,
  filename,
  pageRequest,
}: {
  agreementId: string
  filename: string
  pageRequest: PageRequest | null
}) {
  const api = useApi()
  const query = useQuery(agreementDocumentQueryOptions(api, agreementId))
  return (
    <DocumentPane query={query} filename={filename} pageRequest={pageRequest} />
  )
}
