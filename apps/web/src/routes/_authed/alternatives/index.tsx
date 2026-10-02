import * as React from 'react'
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { AlternativesPanel } from '#/components/alternatives/list/alternatives-panel'
import { useApi } from '#/lib/auth/auth'
import { alternativesQueryOptions } from '#/lib/api/alternatives'
import { companiesQueryOptions } from '#/lib/api/companies'
import type { AlternativeFilters } from '#/lib/api/alternative-types'
import {
  applyAlternativeFilterChange,
  validateAlternativeSearch,
} from '#/lib/alternative-search'

export const Route = createFileRoute('/_authed/alternatives/')({
  component: AlternativesPage,
  staticData: { title: 'Alternatives' },
  validateSearch: validateAlternativeSearch,
})

function AlternativesPage() {
  const api = useApi()
  const navigate = useNavigate({ from: Route.fullPath })
  const filters = Route.useSearch()
  const companies = useQuery(companiesQueryOptions(api))
  const alternatives = useQuery(alternativesQueryOptions(api, filters))

  const onFiltersChange = React.useCallback(
    (changes: Partial<AlternativeFilters>) => {
      void navigate({ search: applyAlternativeFilterChange(filters, changes) })
    },
    [filters, navigate],
  )

  return (
    <AlternativesPanel
      result={alternatives.data}
      loading={alternatives.isPending}
      error={alternatives.isError}
      filters={filters}
      companies={companies.data ?? []}
      onFiltersChange={onFiltersChange}
      onClearFilters={() => {
        void navigate({ search: {} })
      }}
      onPageChange={(page) => {
        void navigate({ search: { ...filters, page } })
      }}
      onSelect={(item) => {
        void navigate({
          to: '/alternatives/$itemId',
          params: { itemId: item.id },
        })
      }}
    />
  )
}
