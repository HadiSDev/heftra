import { describe, expect, it } from 'vitest'
import type { ItemLineRead } from '#/lib/api/alternative-types'
import { DEFAULT_ITEM_LINE_SORT, sortItemLines } from './item-lines'

function line(
  id: string,
  invoice_date: string | null,
  base_amount: string | null,
): ItemLineRead {
  return {
    id,
    invoice_id: `inv-${id}`,
    voucher_id: null,
    invoice_number: null,
    invoice_date,
    item_name: 'Round bar',
    quantity: '1',
    unit: null,
    base_amount,
    net_amount: base_amount,
    base_currency: 'DKK',
  }
}

const LINES = [
  line('a', '2026-08-01', '600.00'),
  line('b', '2026-09-20', '40.00'),
  line('c', null, '1200.00'),
  line('d', '2026-07-01', null),
]

function ids(lines: Array<ItemLineRead>): Array<string> {
  return lines.map((entry) => entry.id)
}

describe('sortItemLines', () => {
  it('puts the newest first by default, undated lines last', () => {
    expect(ids(sortItemLines(LINES, DEFAULT_ITEM_LINE_SORT))).toEqual([
      'b',
      'a',
      'd',
      'c',
    ])
  })

  it('sorts amounts as numbers, either way, lines without one last', () => {
    expect(
      ids(sortItemLines(LINES, { sort: 'amount', order: 'desc' })),
    ).toEqual(['c', 'a', 'b', 'd'])
    expect(ids(sortItemLines(LINES, { sort: 'amount', order: 'asc' }))).toEqual(
      ['b', 'a', 'c', 'd'],
    )
  })

  it('leaves the given list as it was', () => {
    const given = [...LINES]
    sortItemLines(given, { sort: 'amount', order: 'asc' })
    expect(ids(given)).toEqual(['a', 'b', 'c', 'd'])
  })
})
