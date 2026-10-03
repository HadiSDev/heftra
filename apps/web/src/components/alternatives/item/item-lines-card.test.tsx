import type { ReactNode } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import type * as RouterModule from '@tanstack/react-router'
import type { ItemLineRead } from '#/lib/api/alternative-types'
import { ItemLinesCard } from './item-lines-card'

vi.mock('@tanstack/react-router', async (importOriginal) => {
  const actual = await importOriginal<typeof RouterModule>()
  return {
    ...actual,
    Link: ({ children, ...props }: { children?: ReactNode }) => (
      <a {...props}>{children}</a>
    ),
  }
})

afterEach(() => {
  cleanup()
})

function line(id: string, date: string, amount: string): ItemLineRead {
  return {
    id,
    invoice_id: `inv-${id}`,
    voucher_id: `v-${id}`,
    invoice_number: id.toUpperCase(),
    invoice_date: date,
    item_name: 'Round bar',
    quantity: '1',
    unit: 'kg',
    base_amount: amount,
    net_amount: amount,
    base_currency: 'DKK',
  }
}

const LINES = [
  line('a1', '2026-09-20', '40.00'),
  line('a2', '2026-08-01', '600.00'),
]

function invoiceOrder(): Array<string> {
  return screen.getAllByText(/^Invoice /).map((element) => element.textContent)
}

describe('ItemLinesCard', () => {
  it('lists the newest first, and sorts by amount from its header', () => {
    render(<ItemLinesCard companyId="c1" lines={LINES} />)
    expect(invoiceOrder()).toEqual(['Invoice A1 · 1 kg', 'Invoice A2 · 1 kg'])

    fireEvent.click(screen.getByRole('button', { name: 'Excl. VAT' }))
    expect(invoiceOrder()).toEqual(['Invoice A2 · 1 kg', 'Invoice A1 · 1 kg'])

    fireEvent.click(screen.getByRole('button', { name: 'Excl. VAT' }))
    expect(invoiceOrder()).toEqual(['Invoice A1 · 1 kg', 'Invoice A2 · 1 kg'])
  })

  it('shows a line without VAT, with the invoice amount beside it', () => {
    render(
      <ItemLinesCard
        companyId="c1"
        lines={[
          { ...line('a1', '2026-05-10', '484.00'), net_amount: '387.20' },
        ]}
      />,
    )
    expect(screen.getByText(/387\.20/)).toBeTruthy()
    expect(screen.getByText(/484\.00.*incl\. VAT/)).toBeTruthy()
  })
})
