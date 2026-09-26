import { describe, expect, it, vi } from 'vitest'
import {
  spendBreakdownOptions,
  spendInsightsOptions,
  spendOverviewOptions,
  spendTrendOptions,
} from './spend-reports'
import type { ApiClient } from './api-client'

function fakeApi() {
  const get = vi.fn().mockResolvedValue({ rows: [] })
  return { api: { get } as unknown as ApiClient, get }
}

const SCOPE = { from: '2026-07-01', to: '2026-09-26', company_id: 'c1' }

describe('spend report queries', () => {
  it.each([
    [spendOverviewOptions, 'spend-overview'],
    [spendTrendOptions, 'spend-trend'],
    [spendBreakdownOptions, 'spend-breakdown'],
    [spendInsightsOptions, 'spend-insights'],
  ] as const)('asks its endpoint for the scope', async (options, report) => {
    const { api, get } = fakeApi()
    const query = options(api, SCOPE)

    await query.queryFn!({} as never)

    expect(get).toHaveBeenCalledWith(`/api/v1/reports/${report}`, SCOPE)
    expect(query.queryKey).toEqual(['reports', report, SCOPE])
  })

  it('keeps the figures in view while another period loads', () => {
    const { api } = fakeApi()

    expect(spendOverviewOptions(api, SCOPE).placeholderData).toBeDefined()
  })
})
