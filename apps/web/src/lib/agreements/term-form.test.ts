import { describe, expect, it } from 'vitest'
import type { TermRead } from '#/lib/api/agreement-types'
import {
  EMPTY_TERM_VALUES,
  parseTiers,
  termFields,
  termProblem,
  termValues,
} from './term-form'

const PRICE: TermRead = {
  id: 't1',
  agreement_id: 'a1',
  kind: 'agreed_price',
  status: 'draft',
  source: 'ai',
  scope: 'Laptops',
  conditions: null,
  item: 'ThinkPad T14 Gen 5',
  unit: 'unit',
  unit_price: '8000.0000',
  discount_percent: null,
  commitment_amount: null,
  commitment_period: null,
  tiers: null,
  currency: 'DKK',
  scope_category_ids: [],
  quotes: [{ text: 'ThinkPad T14 Gen 5 at DKK 8,000', page: 7 }],
  confidence: '0.9',
  created_at: '2026-09-27T10:00:00Z',
  updated_at: null,
}

describe('termFields', () => {
  it('sends only the fields the kind uses', () => {
    const fields = termFields('agreed_price', {
      ...termValues(PRICE),
      conditions: 'ignored',
      unit_price: '7 950,50',
    })

    expect(fields).toMatchObject({
      scope: 'Laptops',
      item: 'ThinkPad T14 Gen 5',
      unit_price: '7950.50',
      conditions: null,
      discount_percent: null,
      currency: 'DKK',
    })
  })

  it('reads rebate tiers from lines', () => {
    const fields = termFields('volume_commitment', {
      ...EMPTY_TERM_VALUES,
      scope: 'IT equipment',
      commitment_amount: '500000',
      tiers: '100000 = 1%\nnot a tier\n400 000 = 2,5%',
    })

    expect(fields.tiers).toEqual([
      { threshold: '100000', rebate_percent: '1' },
      { threshold: '400000', rebate_percent: '2.5' },
    ])
  })
})

describe('termProblem', () => {
  it('needs the price of an agreed price', () => {
    expect(
      termProblem('agreed_price', { ...termValues(PRICE), unit_price: '' }),
    ).toBe('An agreed price needs the item and its price.')
    expect(termProblem('agreed_price', termValues(PRICE))).toBeNull()
  })

  it('needs a scope', () => {
    expect(termProblem('discount', EMPTY_TERM_VALUES)).toBe(
      'Say what the term covers.',
    )
  })
})

describe('parseTiers', () => {
  it('leaves out lines that are not tiers', () => {
    expect(parseTiers('')).toEqual([])
  })
})
