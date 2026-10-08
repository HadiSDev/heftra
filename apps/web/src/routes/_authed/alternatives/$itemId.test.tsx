import type { ComponentType } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type * as AuthModule from '#/lib/auth/auth'
import type { Principal } from '#/lib/auth/auth'
import type { ItemRead } from '#/lib/api/alternative-types'

import { Route } from './$itemId'

const DEMO: Principal = {
  id: 'u1',
  email: 'demo@heftra.com',
  name: 'Demo',
  role: 'demo',
  isSystemAdmin: false,
  organizationId: 'org1',
  demo: true,
}

const ITEM: ItemRead = {
  id: 'i1',
  company_id: 'c1',
  item_name: 'Rundstål S235JR 20mm',
  description: null,
  unit: 'kg',
  vendor_id: 'v1',
  supplier_name: 'Lemvigh-Müller',
  category_path: ['Materials', 'Steel'],
  spec: {
    item_class: 'material',
    product_type: 'hot-rolled round bar',
    name: 'Round bar S235JR 20mm',
    brand: null,
    model: null,
    part_number: null,
    gtin: null,
    attributes: [],
    pricing_unit: 'kg',
    units_per_line_unit: 1,
    confidence: 0.9,
  },
  spec_source: 'ai',
  spend: '41600.00',
  lines: 12,
  last_bought_on: '2026-05-01',
  quantity: '4000',
  unit_price: '10.40',
  currency: 'DKK',
  price_note: null,
  searched_at: null,
  searching: false,
  alternatives: [],
}

const get = vi.fn()

vi.mock('#/lib/auth/auth', async (importOriginal) => ({
  ...(await importOriginal<typeof AuthModule>()),
  usePrincipal: () => DEMO,
  useApi: () => ({ get }),
}))

const ItemPage = Route.options.component as unknown as ComponentType

beforeEach(() => {
  vi.spyOn(Route, 'useParams').mockReturnValue({ itemId: 'i1' })
  get.mockImplementation((path: string) =>
    Promise.resolve(path.endsWith('/lines') ? [] : ITEM),
  )
})

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('Alternatives item route for the demo login', () => {
  it('offers the search and the specification editor, like an admin', async () => {
    render(
      <QueryClientProvider client={new QueryClient()}>
        <ItemPage />
      </QueryClientProvider>,
    )

    expect(
      await screen.findByRole('button', { name: 'Find cheaper alternatives' }),
    ).toBeTruthy()
    expect(
      screen.getByRole('button', { name: 'Correct the specification' }),
    ).toBeTruthy()
  })
})
