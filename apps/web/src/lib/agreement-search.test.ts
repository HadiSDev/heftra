import { describe, expect, it } from 'vitest'
import type { AgreementRead } from '#/lib/api/agreement-types'
import {
  defaultAgreementTab,
  resolveFindingSort,
  validateAgreementSearch,
} from './agreement-search'

function agreement(
  status: AgreementRead['status'],
  termStatuses: Array<'draft' | 'confirmed' | 'rejected'>,
): Pick<AgreementRead, 'status' | 'terms'> {
  return {
    status,
    terms: termStatuses.map(
      (termStatus) =>
        ({ status: termStatus }) as AgreementRead['terms'][number],
    ),
  }
}

describe('defaultAgreementTab', () => {
  it('stays on the terms while some are still drafts', () => {
    expect(
      defaultAgreementTab(agreement('active', ['confirmed', 'draft'])),
    ).toBe('terms')
  })

  it('opens the report once every term is decided', () => {
    expect(
      defaultAgreementTab(agreement('active', ['confirmed', 'rejected'])),
    ).toBe('report')
  })

  it('shows the terms of an agreement that is not active', () => {
    expect(defaultAgreementTab(agreement('review', ['draft']))).toBe('terms')
    expect(defaultAgreementTab(undefined)).toBe('terms')
  })
})

describe('findings sort', () => {
  it('keeps a known sort and order from the URL and drops anything else', () => {
    expect(
      validateAgreementSearch({ sort: 'amount', order: 'asc', view: 'all' }),
    ).toEqual({ tab: undefined, view: 'all', sort: 'amount', order: 'asc' })
    expect(validateAgreementSearch({ sort: 'reason', order: 'up' })).toEqual({
      tab: undefined,
      view: undefined,
      sort: undefined,
      order: undefined,
    })
  })

  it('lists rule breaks first until another sort is chosen', () => {
    expect(resolveFindingSort({})).toEqual({ sort: 'severity', order: 'desc' })
  })

  it('starts names A–Z and figures largest first', () => {
    expect(resolveFindingSort({ sort: 'item' }).order).toBe('asc')
    expect(resolveFindingSort({ sort: 'supplier' }).order).toBe('asc')
    expect(resolveFindingSort({ sort: 'spent_on' }).order).toBe('desc')
    expect(resolveFindingSort({ sort: 'amount', order: 'asc' }).order).toBe(
      'asc',
    )
  })
})
