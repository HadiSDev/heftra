import { describe, expect, it } from 'vitest'
import type { AgreementRead } from '#/lib/api/agreement-types'
import { defaultAgreementTab } from './agreement-search'

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
