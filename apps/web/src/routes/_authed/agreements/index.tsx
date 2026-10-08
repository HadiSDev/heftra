import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AgreementsPanel } from '#/components/agreements/list/agreements-panel'
import {
  defaultAgreementOrder,
  resolveAgreementSort,
  validateAgreementListSearch,
} from '#/lib/agreements/list-sort'
import { ApiError } from '#/lib/api/api-client'
import {
  agreementsQueryOptions,
  uploadAgreementMutation,
} from '#/lib/api/agreements'
import { companiesQueryOptions } from '#/lib/api/companies'
import { canManageCompanies, useApi, usePrincipal } from '#/lib/auth/auth'
import { nextSort } from '#/lib/sorting'

export const Route = createFileRoute('/_authed/agreements/')({
  component: AgreementsPage,
  staticData: { title: 'Agreements' },
  validateSearch: validateAgreementListSearch,
})

function AgreementsPage() {
  const api = useApi()
  const navigate = useNavigate({ from: Route.fullPath })
  const { sort, order } = resolveAgreementSort(Route.useSearch())
  const queryClient = useQueryClient()
  const principal = usePrincipal()
  const canUpload = canManageCompanies(principal) && !principal.demo
  const agreements = useQuery(agreementsQueryOptions(api))
  const companies = useQuery({
    ...companiesQueryOptions(api),
    enabled: canUpload,
  })
  const upload = useMutation(uploadAgreementMutation(api, queryClient))

  return (
    <AgreementsPanel
      agreements={agreements.data}
      error={agreements.isError}
      onRetry={() => {
        void agreements.refetch()
      }}
      sort={sort}
      order={order}
      onSort={(column) => {
        void navigate({
          search: nextSort({ sort, order }, column, defaultAgreementOrder),
        })
      }}
      upload={
        canUpload
          ? {
              companies: (companies.data ?? []).map((company) => ({
                id: company.id,
                name: company.name,
              })),
              onUpload: async (companyId, file, onProgress) => {
                try {
                  await upload.mutateAsync({ companyId, file, onProgress })
                } catch (error) {
                  throw new Error(
                    error instanceof ApiError ? error.detail : 'Upload failed',
                  )
                }
              },
            }
          : null
      }
    />
  )
}
