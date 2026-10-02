import type { ReactNode } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react'
import type * as RouterModule from '@tanstack/react-router'
import type {
  AlternativeRead,
  AlternativesPage,
  ItemLineRead,
  ItemRead,
  ItemSummary,
} from '#/lib/api/alternative-types'
import { AlternativesPanel } from './list/alternatives-panel'
import { ItemPanel } from './item/item-panel'
import { LineAlternativesView } from './line/line-alternatives-view'

vi.mock('@tanstack/react-router', async (importOriginal) => {
  const actual = await importOriginal<typeof RouterModule>()
  return {
    ...actual,
    Link: ({
      to,
      children,
      params,
      search,
      ...props
    }: {
      to: string
      children?: ReactNode
      params?: Record<string, string>
      search?: Record<string, string>
    }) => {
      const path = Object.entries(params ?? {}).reduce(
        (href, [key, value]) => href.replace(`$${key}`, value),
        to,
      )
      const query = search ? `?${new URLSearchParams(search).toString()}` : ''
      return (
        <a href={`${path}${query}`} {...props}>
          {children}
        </a>
      )
    },
  }
})

afterEach(() => {
  cleanup()
})

const ALTERNATIVE: AlternativeRead = {
  id: 'a1',
  item_id: 'i1',
  source: 'history',
  match: 'equivalent',
  name: 'Round bar S355J2 20mm',
  unit_price: '9.10',
  currency: 'DKK',
  saving_yearly: '4200.00',
  saving_percent: '12.50',
  comparison: [
    {
      name: 'steel_grade',
      item: 'S235JR',
      candidate: 'S355J2',
      verdict: 'better',
      reason: 'A higher grade.',
    },
    {
      name: 'diameter',
      item: '20 mm',
      candidate: '20 mm',
      verdict: 'same',
      reason: '',
    },
  ],
  origin: {
    supplier: 'Sanistål',
    company: 'Acme DK',
    last_bought_on: '2026-05-01',
  },
  agreement_notes: [
    {
      kind: 'off_contract',
      agreement_id: 'ag1',
      term_id: 't1',
      text: 'Buying it here would be off contract under Lemvigh, which requires Lemvigh-Müller for steel.',
    },
  ],
  review_status: 'open',
  dismiss_reason: null,
  review_note: null,
  reviewed_by_name: null,
  reviewed_at: null,
  found_at: '2026-06-01T10:00:00Z',
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
    attributes: [
      {
        name: 'steel_grade',
        kind: 'tiered',
        value: 'S235JR',
        number: null,
        unit: null,
        direction: 'more',
        family: 'EN 10025',
        tier: 'S235',
        generation: null,
      },
    ],
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
  searched_at: '2026-06-01T10:00:00Z',
  searching: false,
  alternatives: [ALTERNATIVE],
}

function summary(fields: Partial<ItemSummary>): ItemSummary {
  return {
    id: 'i1',
    company_id: 'c1',
    name: 'Round bar',
    supplier_name: 'Lemvigh-Müller',
    item_class: 'material',
    pricing_unit: 'kg',
    unit_price: '10.40',
    quantity: '4000',
    currency: 'DKK',
    alternatives: 1,
    best: ALTERNATIVE,
    ...fields,
  }
}

function page(fields: Partial<AlternativesPage>): AlternativesPage {
  return {
    items: [],
    page: 1,
    page_size: 25,
    total: 0,
    total_saving: null,
    currency: null,
    searched_items: 0,
    ...fields,
  }
}

function renderPanel(result: AlternativesPage, filters = {}) {
  const onSelect = vi.fn()
  render(
    <AlternativesPanel
      result={result}
      loading={false}
      error={false}
      filters={filters}
      companies={[]}
      onFiltersChange={vi.fn()}
      onClearFilters={vi.fn()}
      onPageChange={vi.fn()}
      onSelect={onSelect}
    />,
  )
  return onSelect
}

describe('AlternativesPanel', () => {
  it('leads with the possible saving and lists the items', () => {
    const onSelect = renderPanel(
      page({
        items: [summary({ id: 'laptops', name: 'ThinkPad T14' }), summary({})],
        total: 2,
        total_saving: '4932.00',
        currency: 'DKK',
      }),
    )

    expect(
      screen.getByText('Possible yearly saving').parentElement?.textContent,
    ).toContain('4,932')
    fireEvent.click(screen.getByText('ThinkPad T14'))
    expect(onSelect).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'laptops' }),
    )
  })

  it('says when nothing was searched yet', () => {
    renderPanel(page({}))
    expect(screen.getByText('Nothing searched yet')).toBeTruthy()
  })

  it('says when searches found nothing cheaper', () => {
    renderPanel(page({ searched_items: 40 }))
    expect(screen.getByText('Nothing cheaper found')).toBeTruthy()
  })

  it('offers to clear filters that match nothing', () => {
    renderPanel(page({ searched_items: 40 }), { source: 'marketplace' })
    expect(screen.getByRole('button', { name: 'Clear filters' })).toBeTruthy()
  })
})

const LINES: Array<ItemLineRead> = [
  {
    id: 'l2',
    invoice_id: 'inv2',
    voucher_id: null,
    invoice_number: 'A2',
    invoice_date: '2026-09-20',
    item_name: 'Round bar',
    quantity: '40',
    unit: 'kg',
    base_amount: '400.00',
    base_currency: 'DKK',
  },
  {
    id: 'l1',
    invoice_id: 'inv1',
    voucher_id: '4821',
    invoice_number: 'A1',
    invoice_date: '2026-08-01',
    item_name: 'Round bar',
    quantity: '60',
    unit: 'kg',
    base_amount: '600.00',
    base_currency: 'DKK',
  },
]

function renderItem(
  item: ItemRead,
  canManage = true,
  lines: Array<ItemLineRead> | undefined | null = LINES,
) {
  const props = {
    onSearch: vi.fn(),
    onSaveSpec: vi.fn(async () => {}),
    onReview: vi.fn(async () => {}),
  }
  render(
    <ItemPanel
      item={item}
      lines={lines}
      canManage={canManage}
      searchPending={false}
      {...props}
    />,
  )
  return props
}

describe('ItemPanel', () => {
  it('lists the spend lines, opening a posted one in Spend Lines', () => {
    renderItem(ITEM)
    const card = screen.getByRole('heading', { name: 'Spend lines' })
      .parentElement!.parentElement!
    const open = within(card).getByRole('link', { name: /Open the voucher/ })
    expect(open.getAttribute('href')).toBe(
      `/invoice-lines?company_id=${ITEM.company_id}&voucher=4821&tab=lines`,
    )
    expect(within(card).getByText('Not posted yet')).toBeTruthy()
    expect(within(card).getByText('2 in the last 12 months')).toBeTruthy()
  })

  it('says when the lines could not be loaded', () => {
    renderItem(ITEM, true, null)
    expect(screen.getByText('The lines could not be loaded.')).toBeTruthy()
  })

  it('shows the attributes side by side and what switching would break', () => {
    renderItem(ITEM)

    const card = screen.getByRole('article', {
      name: 'Round bar S355J2 20mm',
    })
    expect(within(card).getByText('S355J2')).toBeTruthy()
    expect(within(card).getByText('Better')).toBeTruthy()
    expect(within(card).getByText(/off contract under Lemvigh/)).toBeTruthy()
    expect(
      within(card).getByRole('link', { name: 'Open the agreement' }),
    ).toHaveProperty('href', expect.stringContaining('/agreements/ag1'))
    expect(
      within(card).getByText(/Bought from Sanistål by Acme DK/),
    ).toBeTruthy()
  })

  it('dismisses an alternative with its reason', async () => {
    const props = renderItem(ITEM)

    fireEvent.click(screen.getByRole('button', { name: 'Dismiss' }))
    fireEvent.change(screen.getByRole('textbox', { name: 'Note' }), {
      target: { value: 'Not an approved supplier' },
    })
    fireEvent.click(
      within(screen.getByRole('dialog')).getByRole('button', {
        name: 'Dismiss',
      }),
    )

    await waitFor(() => {
      expect(props.onReview).toHaveBeenCalledWith('a1', {
        review_status: 'dismissed',
        dismiss_reason: 'not_equivalent',
        note: 'Not an approved supplier',
      })
    })
  })

  it('asks for a search, and shows one running', () => {
    const props = renderItem(ITEM)
    fireEvent.click(
      screen.getByRole('button', { name: 'Find cheaper alternatives' }),
    )
    expect(props.onSearch).toHaveBeenCalled()

    cleanup()
    renderItem({ ...ITEM, searching: true })
    expect(screen.getByText('Searching for cheaper alternatives…')).toBeTruthy()
    expect(
      screen
        .getByRole('button', { name: 'Find cheaper alternatives' })
        .hasAttribute('disabled'),
    ).toBe(true)
  })

  it('corrects the specification', async () => {
    const props = renderItem(ITEM)

    fireEvent.click(
      screen.getByRole('button', { name: 'Correct the specification' }),
    )
    fireEvent.change(screen.getByDisplayValue('1'), {
      target: { value: '6' },
    })
    fireEvent.click(
      screen.getByRole('button', { name: 'Save and search again' }),
    )

    await waitFor(() => {
      expect(props.onSaveSpec).toHaveBeenCalledWith(
        expect.objectContaining({
          units_per_line_unit: 6,
          attributes: [expect.objectContaining({ name: 'steel_grade' })],
        }),
      )
    })
  })

  it('gives a viewer no actions', () => {
    renderItem(ITEM, false)

    expect(screen.queryByRole('button', { name: 'Dismiss' })).toBeNull()
    expect(
      screen.queryByRole('button', { name: 'Find cheaper alternatives' }),
    ).toBeNull()
    expect(
      screen.queryByRole('button', { name: 'Correct the specification' }),
    ).toBeNull()
  })
})

describe('LineAlternativesView', () => {
  it('offers a manager a search for a line not looked at yet', () => {
    const onFind = vi.fn()
    render(
      <LineAlternativesView
        item={null}
        canManage
        pending={false}
        error={null}
        onFind={onFind}
      />,
    )

    fireEvent.click(
      screen.getByRole('button', { name: 'Find cheaper alternatives' }),
    )
    expect(onFind).toHaveBeenCalled()
  })

  it('shows the best saving and links to the alternatives', () => {
    render(
      <LineAlternativesView
        item={ITEM}
        canManage={false}
        pending={false}
        error={null}
        onFind={vi.fn()}
      />,
    )

    expect(screen.getByText(/Up to/).textContent).toContain('4,200')
    expect(
      screen.getByRole('link', { name: 'See the alternatives' }),
    ).toHaveProperty('href', expect.stringContaining('/alternatives/i1'))
  })
})
