import { createFileRoute } from '@tanstack/react-router'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AgreementsPanel } from '#/components/agreements/list/agreements-panel'
import { ApiError } from '#/lib/api/api-client'
import {
  agreementsQueryOptions,
  uploadAgreementMutation,
} from '#/lib/api/agreements'
import { companiesQueryOptions } from '#/lib/api/companies'
import { canManageCompanies, useApi, usePrincipal } from '#/lib/auth/auth'

export const Route = createFileRoute('/_authed/agreements/')({
  component: AgreementsPage,
  staticData: { title: 'Agreements' },
})

function AgreementsPage() {
  const api = useApi()
  const queryClient = useQueryClient()
  const canManage = canManageCompanies(usePrincipal())
  const agreements = useQuery(agreementsQueryOptions(api))
  const companies = useQuery({
    ...companiesQueryOptions(api),
    enabled: canManage,
  })
  const upload = useMutation(uploadAgreementMutation(api, queryClient))

  return (
    <AgreementsPanel
      agreements={agreements.data}
      error={agreements.isError}
      onRetry={() => {
        void agreements.refetch()
      }}
      upload={
        canManage
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
