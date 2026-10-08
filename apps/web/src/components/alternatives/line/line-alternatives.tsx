import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError } from '#/lib/api/api-client'
import {
  findLineAlternativesMutation,
  lineItemQueryOptions,
} from '#/lib/api/alternatives'
import type { InvoiceLineRead } from '#/lib/api/types'
import { useApi } from '#/lib/auth/auth'
import { LineAlternativesView } from './line-alternatives-view'

function notStored(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404
}

/** The line's alternatives section, loading its item and asking for a search. */
export function LineAlternatives({
  line,
  canManage,
}: {
  line: InvoiceLineRead
  canManage: boolean
}) {
  const api = useApi()
  const queryClient = useQueryClient()
  const item = useQuery(lineItemQueryOptions(api, line.id))
  const find = useMutation(findLineAlternativesMutation(api, queryClient))
  const loaded = item.isError && notStored(item.error) ? null : item.data
  return (
    <LineAlternativesView
      item={item.isPending ? undefined : (loaded ?? null)}
      canManage={canManage}
      pending={find.isPending}
      error={
        find.error instanceof ApiError
          ? find.error.detail
          : find.error
            ? 'Not queued'
            : null
      }
      onFind={() => {
        find.mutate(line.id)
      }}
    />
  )
}
