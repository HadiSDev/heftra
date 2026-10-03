import * as React from 'react'
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { AlternativesPanel } from '#/components/alternatives/list/alternatives-panel'
import { useApi } from '#/lib/auth/auth'
import { alternativesQueryOptions } from '#/lib/api/alternatives'
import { companiesQueryOptions } from '#/lib/api/companies'
import type {
  AlternativeFilters,
  AlternativeSort,
} from '#/lib/api/alternative-types'
import { nextSort } from '#/lib/sorting'
import {
  applyAlternativeFilterChange,
  canSortByUnitPrice,
  defaultOrder,
  resolveAlternativeSort,
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
  const unitPriceSortable = canSortByUnitPrice(
    companies.data ?? [],
    filters.company_id,
  )
  const { sort, order } = resolveAlternativeSort(filters, unitPriceSortable)
  const alternatives = useQuery({
    ...alternativesQueryOptions(api, { ...filters, sort, order }),
    enabled: companies.isSuccess,
  })

  const onFiltersChange = React.useCallback(
    (changes: Partial<AlternativeFilters>) => {
      void navigate({ search: applyAlternativeFilterChange(filters, changes) })
    },
    [filters, navigate],
  )

  function onSort(column: AlternativeSort) {
    onFiltersChange(nextSort({ sort, order }, column, defaultOrder))
  }

  return (
    <AlternativesPanel
      result={alternatives.data}
      loading={companies.isPending || alternatives.isPending}
      error={companies.isError || alternatives.isError}
      filters={filters}
      sort={sort}
      order={order}
      unitPriceSortable={unitPriceSortable}
      companies={companies.data ?? []}
      onFiltersChange={onFiltersChange}
      onClearFilters={() => {
        void navigate({ search: {} })
      }}
      onSort={onSort}
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
