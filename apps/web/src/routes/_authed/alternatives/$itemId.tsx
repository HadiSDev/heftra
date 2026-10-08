import { createFileRoute } from '@tanstack/react-router'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Card, Skeleton } from '#/components/ui'
import { ItemPanel } from '#/components/alternatives/item/item-panel'
import { ApiError } from '#/lib/api/api-client'
import {
  findAlternativesMutation,
  itemLinesQueryOptions,
  itemQueryOptions,
  reviewAlternativeMutation,
  updateSpecificationMutation,
} from '#/lib/api/alternatives'
import { canManageCompanies, useApi, usePrincipal } from '#/lib/auth/auth'

export const Route = createFileRoute('/_authed/alternatives/$itemId')({
  component: ItemPage,
  staticData: { title: 'Alternatives' },
})

function message(error: unknown, fallback: string): Error {
  return new Error(error instanceof ApiError ? error.detail : fallback)
}

function ItemPage() {
  const { itemId } = Route.useParams()
  const api = useApi()
  const queryClient = useQueryClient()
  const principal = usePrincipal()
  const canManage = canManageCompanies(principal)
  const item = useQuery(itemQueryOptions(api, itemId))
  const lines = useQuery(itemLinesQueryOptions(api, itemId))
  const search = useMutation(findAlternativesMutation(api, queryClient))
  const saveSpec = useMutation(updateSpecificationMutation(api, queryClient))
  const review = useMutation(reviewAlternativeMutation(api, queryClient))

  if (item.isError) {
    return (
      <Card className="flex items-center justify-between gap-4 p-6">
        <p className="text-sm text-destructive">
          {item.error instanceof ApiError && item.error.status === 404
            ? 'This item doesn’t exist, or isn’t one of yours.'
            : 'The item could not be loaded.'}
        </p>
        <Button size="sm" variant="outline" onClick={() => void item.refetch()}>
          Try again
        </Button>
      </Card>
    )
  }
  if (!item.data) {
    return (
      <div className="flex flex-col gap-4" aria-label="Loading the item">
        <Skeleton className="h-16 w-1/2" />
        <Skeleton className="h-96 w-full rounded-2xl" />
      </div>
    )
  }
  return (
    <ItemPanel
      item={item.data}
      lines={lines.isError ? null : lines.data}
      canManage={canManage}
      demo={principal.demo}
      searchPending={search.isPending}
      onSearch={() => {
        search.mutate(itemId)
      }}
      onSaveSpec={async (spec) => {
        try {
          await saveSpec.mutateAsync({ itemId, spec })
        } catch (error) {
          throw message(error, 'Not saved')
        }
      }}
      onReview={async (alternativeId, alternativeReview) => {
        try {
          await review.mutateAsync({ alternativeId, review: alternativeReview })
        } catch (error) {
          throw message(error, 'Not saved')
        }
      }}
    />
  )
}
