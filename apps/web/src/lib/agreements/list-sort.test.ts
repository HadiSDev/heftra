import { describe, expect, it } from 'vitest'
import type { AgreementSummaryRead } from '#/lib/api/agreement-types'
import {
  defaultAgreementOrder,
  resolveAgreementSort,
  sortAgreements,
  validateAgreementListSearch,
} from './list-sort'

function summary(
  id: string,
  overrides: Partial<AgreementSummaryRead> = {},
): AgreementSummaryRead {
  return {
    id,
    company_id: 'c1',
    title: id,
    reference: null,
    supplier: null,
    supplier_name: null,
    starts_on: null,
    ends_on: null,
    currency: 'DKK',
    status: 'active',
    expired: false,
    read_error: null,
    analysed_at: null,
    created_at: '2026-09-01T10:00:00Z',
    open_rule_breaks: 0,
    rule_break_amount: '0',
    base_currency: 'DKK',
    ...overrides,
  }
}

function ids(agreements: Array<AgreementSummaryRead>): Array<string> {
  return agreements.map((agreement) => agreement.id)
}

describe('validateAgreementListSearch', () => {
  it('keeps a known sort and order and drops anything else', () => {
    expect(
      validateAgreementListSearch({ sort: 'supplier', order: 'desc' }),
    ).toEqual({ sort: 'supplier', order: 'desc' })
    expect(
      validateAgreementListSearch({ sort: 'reason', order: 'sideways' }),
    ).toEqual({ sort: undefined, order: undefined })
  })
})

describe('resolveAgreementSort', () => {
  it('lists the newest first until a column is chosen', () => {
    expect(resolveAgreementSort({})).toEqual({
      sort: 'created_at',
      order: 'desc',
    })
  })

  it('starts a column in its own order', () => {
    expect(resolveAgreementSort({ sort: 'title' }).order).toBe('asc')
    expect(resolveAgreementSort({ sort: 'starts_on' }).order).toBe('desc')
    expect(defaultAgreementOrder('open_rule_breaks')).toBe('desc')
  })
})

describe('sortAgreements', () => {
  it('sorts by supplier with unlinked agreements last either way', () => {
    const agreements = [
      summary('none'),
      summary('proshop', { supplier_name: 'Proshop A/S' }),
      summary('atea', {
        supplier: { vendor_id: 'v1', name: 'atea A/S' },
        supplier_name: 'Atea',
      }),
    ]

    expect(
      ids(sortAgreements(agreements, { sort: 'supplier', order: 'asc' })),
    ).toEqual(['atea', 'proshop', 'none'])
    expect(
      ids(sortAgreements(agreements, { sort: 'supplier', order: 'desc' })),
    ).toEqual(['proshop', 'atea', 'none'])
  })

  it('sorts by open rule breaks, then their amount, inactive agreements last', () => {
    const agreements = [
      summary('review', { status: 'review', open_rule_breaks: 9 }),
      summary('small', { open_rule_breaks: 2, rule_break_amount: '100' }),
      summary('large', { open_rule_breaks: 2, rule_break_amount: '900' }),
      summary('many', { open_rule_breaks: 5, rule_break_amount: '50' }),
    ]

    expect(
      ids(
        sortAgreements(agreements, { sort: 'open_rule_breaks', order: 'desc' }),
      ),
    ).toEqual(['many', 'large', 'small', 'review'])
  })

  it('puts agreements needing attention first by status, expired ones last', () => {
    const agreements = [
      summary('expired', { expired: true }),
      summary('active'),
      summary('failed', { status: 'failed' }),
      summary('review', { status: 'review' }),
    ]

    expect(
      ids(sortAgreements(agreements, { sort: 'status', order: 'asc' })),
    ).toEqual(['review', 'failed', 'active', 'expired'])
  })

  it('breaks ties newest first', () => {
    const agreements = [
      summary('old', { title: 'Same', created_at: '2026-01-01T00:00:00Z' }),
      summary('new', { title: 'Same', created_at: '2026-06-01T00:00:00Z' }),
    ]

    expect(
      ids(sortAgreements(agreements, { sort: 'title', order: 'asc' })),
    ).toEqual(['new', 'old'])
  })
})
