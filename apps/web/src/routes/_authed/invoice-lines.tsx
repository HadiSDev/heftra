import * as React from 'react'
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { EntriesPanel } from '#/components/entries/entries-panel'
import { canManageCompanies, useApi, usePrincipal } from '#/lib/auth/auth'
import { LineAlternatives } from '#/components/alternatives/line/line-alternatives'
import { companiesQueryOptions } from '#/lib/api/companies'
import {
  voucherAuditQueryOptions,
  voucherDetailQueryOptions,
  voucherGroupsQueryOptions,
  voucherSummaryQueryOptions,
} from '#/lib/api/entries'
import type { VoucherKey } from '#/lib/api/entries'
import {
  createInvoiceLineMutation,
  deleteInvoiceLineMutation,
  reprocessInvoiceMutation,
  updateInvoiceLineMutation,
  updateInvoiceMutation,
  verifyInvoiceLineMutation,
  verifyInvoiceMutation,
} from '#/lib/api/invoices'
import {
  emissionSectorsQueryOptions,
  voucherEmissionsQueryOptions,
} from '#/lib/api/emissions'
import { entriesSummaryOptions } from '#/lib/api/reports'
import { spendTreeQueryOptions } from '#/lib/api/spend-trees'
import {
  applyFilterChange,
  applySortChange,
  applyVoucherSelection,
  defaultVoucherOrder,
  listableEntryTypes,
  resolveVoucherSort,
  validateEntrySearch,
} from '#/lib/entry-search'
import type { VoucherSort } from '#/lib/api/types'
import { nextSort } from '#/lib/sorting'
import { canSortBySpend } from '#/lib/supplier-search'
import { vendorsQueryOptions } from '#/lib/api/vendors'
import { useDebouncedValue } from '#/lib/use-debounced-value'

export const Route = createFileRoute('/_authed/invoice-lines')({
  component: EntriesPage,
  staticData: { title: 'Spend Lines' },
  validateSearch: validateEntrySearch,
})

function EntriesPage() {
  const api = useApi()
  const principal = usePrincipal()
  const navigate = useNavigate({ from: Route.fullPath })
  const queryClient = useQueryClient()
  const filters = Route.useSearch()

  const [vendorQuery, setVendorQuery] = React.useState('')
  const [sectorQuery, setSectorQuery] = React.useState('')
  const sectorSearchText = useDebouncedValue(sectorQuery, 250)

  const voucherKey: VoucherKey = {
    voucher: filters.voucher,
    entry: filters.entry,
  }
  const voucherOpen =
    filters.voucher !== undefined || filters.entry !== undefined

  const companies = useQuery(companiesQueryOptions(api))
  const amountSortable = canSortBySpend(
    companies.data ?? [],
    filters.company_id,
  )
  const { sort, order } = resolveVoucherSort(filters, amountSortable)
  const groups = useQuery({
    ...voucherGroupsQueryOptions(api, { ...filters, sort, order }),
    enabled: filters.sort !== 'amount' || companies.isSuccess,
  })
  const coverage = useQuery(voucherSummaryQueryOptions(api, filters))
  const emissions = useQuery(voucherEmissionsQueryOptions(api, filters))
  const vendors = useQuery(vendorsQueryOptions(api, { q: vendorQuery }))
  const summary = useQuery(entriesSummaryOptions(api))
  const voucherDetail = useQuery(voucherDetailQueryOptions(api, voucherKey))
  const voucherAudit = useQuery(voucherAuditQueryOptions(api, voucherKey))

  const openCompanyId = voucherDetail.data?.invoice?.company_id ?? null
  const openCompany = companies.data?.find((c) => c.id === openCompanyId)
  const sectors = useQuery({
    ...emissionSectorsQueryOptions(api, sectorSearchText),
    enabled: voucherOpen,
  })
  const spendTree = useQuery(
    spendTreeQueryOptions(api, openCompany?.spend_tree_id ?? null),
  )
  const spendTreeNodes = openCompany
    ? openCompany.spend_tree_id === null
      ? []
      : (spendTree.data?.nodes ?? null)
    : null

  const verifyLine = useMutation(verifyInvoiceLineMutation(api, queryClient))
  const updateHeader = useMutation(updateInvoiceMutation(api, queryClient))
  const verifyHeader = useMutation(verifyInvoiceMutation(api, queryClient))
  const updateLine = useMutation(updateInvoiceLineMutation(api, queryClient))
  const createLine = useMutation(createInvoiceLineMutation(api, queryClient))
  const deleteLine = useMutation(deleteInvoiceLineMutation(api, queryClient))
  const reprocess = useMutation(reprocessInvoiceMutation(api, queryClient))

  function onSort(column: VoucherSort) {
    void navigate({
      search: applySortChange(
        filters,
        nextSort({ sort, order }, column, defaultVoucherOrder),
      ),
    })
  }

  const entryTypes = React.useMemo(
    () =>
      listableEntryTypes(
        (summary.data?.rows ?? []).map((row) => row.entry_type),
      ),
    [summary.data],
  )

  return (
    <EntriesPanel
      result={groups.data}
      coverage={coverage.isError ? [] : coverage.data?.rows}
      emissions={{
        summary: emissions.data,
        error: emissions.isError,
        onRetry: () => void emissions.refetch(),
      }}
      sectorSearch={{
        available:
          emissions.data === undefined
            ? undefined
            : emissions.data.factor_set !== null,
        sectors: sectors.data,
        onSearch: setSectorQuery,
      }}
      loading={groups.isPending}
      error={groups.isError}
      filters={filters}
      companies={companies.data ?? []}
      vendors={vendors.data?.items ?? []}
      entryTypes={entryTypes}
      onFiltersChange={(changes) =>
        navigate({ search: applyFilterChange(filters, changes) })
      }
      onClearFilters={() => navigate({ search: {} })}
      onPageChange={(page) => navigate({ search: { ...filters, page } })}
      sort={sort}
      order={order}
      amountSortable={amountSortable}
      onSort={onSort}
      onVendorSearch={setVendorQuery}
      voucherDetail={voucherDetail.data}
      voucherLoading={voucherDetail.isPending && voucherOpen}
      auditRows={voucherAudit.data ?? []}
      auditLoading={voucherAudit.isPending && voucherOpen}
      tab={filters.tab ?? 'details'}
      onTabChange={(tab) => navigate({ search: { ...filters, tab } })}
      onSelectEntry={(key) =>
        navigate({ search: applyVoucherSelection(filters, key) })
      }
      onVerifyLine={async (lineId, corrections) => {
        await verifyLine.mutateAsync({ id: lineId, corrections })
      }}
      spendTreeNodes={spendTreeNodes}
      companySettingsHref={openCompanyId ? `/settings/companies` : undefined}
      onUpdateHeader={async (invoiceId, changes) => {
        await updateHeader.mutateAsync({ id: invoiceId, body: changes })
      }}
      onVerifyHeader={async (invoiceId, changes) => {
        await verifyHeader.mutateAsync({ id: invoiceId, body: changes })
      }}
      onUpdateLine={async (lineId, changes) => {
        await updateLine.mutateAsync({ id: lineId, body: changes })
      }}
      onCreateLine={async (invoiceId) => {
        await createLine.mutateAsync({ invoiceId, body: {} })
      }}
      onDeleteLine={async (lineId) => {
        await deleteLine.mutateAsync({ id: lineId })
      }}
      onReprocess={async (invoiceId) => {
        await reprocess.mutateAsync({ id: invoiceId })
      }}
      canManage={canManageCompanies(principal)}
      renderLineExtra={(line) => (
        <LineAlternatives
          line={line}
          canManage={canManageCompanies(principal)}
        />
      )}
    />
  )
}
