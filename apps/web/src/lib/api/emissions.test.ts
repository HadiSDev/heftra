import { describe, expect, it, vi } from 'vitest'
import {
  emissionSectorsQueryOptions,
  voucherEmissionsQueryOptions,
} from './emissions'
import type { ApiClient } from './api-client'

function fakeApi() {
  const get = vi.fn().mockResolvedValue({})
  return { api: { get } as unknown as ApiClient, get }
}

describe('emission queries', () => {
  it('asks for the listed vouchers’ emissions under the list’s filters, not its page, sort or drawer', async () => {
    const { api, get } = fakeApi()
    const query = voucherEmissionsQueryOptions(api, {
      vendor_id: 'v1',
      page: 3,
      sort: 'amount',
      order: 'asc',
      voucher: '4821',
      tab: 'lines',
    })

    await query.queryFn!({} as never)

    expect(get).toHaveBeenCalledWith('/api/v1/erp-entries/vouchers/emissions', {
      vendor_id: 'v1',
    })
    expect(query.queryKey).toEqual([
      'erp-entries',
      'emissions',
      { vendor_id: 'v1' },
    ])
  })

  it('searches sectors by the trimmed text', async () => {
    const { api, get } = fakeApi()
    const query = emissionSectorsQueryOptions(api, '  hosting ')

    await query.queryFn!({} as never)

    expect(get).toHaveBeenCalledWith('/api/v1/emission-sectors', {
      q: 'hosting',
    })
    expect(query.queryKey).toEqual(['emission-sectors', 'hosting'])
  })
})
