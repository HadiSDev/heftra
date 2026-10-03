import { describe, expect, it } from 'vitest'
import {
  applyFilterChange,
  applySortChange,
  applyVoucherSelection,
  defaultVoucherOrder,
  listableEntryTypes,
  resolveVoucherSort,
  validateEntrySearch,
} from './entry-search'

describe('validateEntrySearch', () => {
  it('reads every filter from the URL', () => {
    expect(
      validateEntrySearch({
        company_id: 'c1',
        entry_type: 'purchase_invoice',
        status: 'failed',
        vendor_id: 'v1',
        from: '2026-01-01',
        to: '2026-01-31',
        page: '3',
      }),
    ).toEqual({
      company_id: 'c1',
      entry_type: 'purchase_invoice',
      status: 'failed',
      vendor_id: 'v1',
      from: '2026-01-01',
      to: '2026-01-31',
      page: 3,
    })
  })

  it('leaves unset filters undefined rather than empty strings', () => {
    const parsed = validateEntrySearch({})
    expect(Object.values(parsed).every((value) => value === undefined)).toBe(
      true,
    )
  })

  it('treats an empty string as unset, so a cleared filter leaves the URL', () => {
    expect(validateEntrySearch({ company_id: '', status: '' })).toMatchObject({
      company_id: undefined,
      status: undefined,
    })
  })

  it('drops page 1 and junk pages, keeping the default URL clean', () => {
    expect(validateEntrySearch({ page: '1' }).page).toBeUndefined()
    expect(validateEntrySearch({ page: 'abc' }).page).toBeUndefined()
    expect(validateEntrySearch({ page: '0' }).page).toBeUndefined()
    expect(validateEntrySearch({ page: '4' }).page).toBe(4)
  })

  it('carries the needs-review flag and the document filter', () => {
    expect(
      validateEntrySearch({ needs_review: 'true', document: 'mismatch' }),
    ).toMatchObject({ needs_review: true, document: 'mismatch' })
    expect(
      validateEntrySearch({ needs_review: true, document: 'failed' }),
    ).toMatchObject({ needs_review: true, document: 'failed' })
  })

  it('drops a document filter or flag it does not know', () => {
    const parsed = validateEntrySearch({ needs_review: 'no', document: 'lost' })
    expect(parsed.needs_review).toBeUndefined()
    expect(parsed.document).toBeUndefined()
  })

  it('carries the open voucher and tab', () => {
    expect(
      validateEntrySearch({ voucher: '4821', tab: 'activity' }),
    ).toMatchObject({
      voucher: '4821',
      tab: 'activity',
    })
  })

  it('carries the sort and its order', () => {
    expect(
      validateEntrySearch({ sort: 'vendor_name', order: 'asc' }),
    ).toMatchObject({ sort: 'vendor_name', order: 'asc' })
  })

  it('drops a sort or order it does not know', () => {
    const parsed = validateEntrySearch({ sort: 'emissions', order: 'up' })
    expect(parsed.sort).toBeUndefined()
    expect(parsed.order).toBeUndefined()
  })

  it('drops an unknown tab rather than trusting the URL', () => {
    expect(
      validateEntrySearch({ voucher: '4821', tab: 'evil' }).tab,
    ).toBeUndefined()
  })
})

describe('applyFilterChange', () => {
  it('merges the change over the existing filters', () => {
    expect(
      applyFilterChange({ company_id: 'c1' }, { status: 'failed' }),
    ).toMatchObject({
      company_id: 'c1',
      status: 'failed',
    })
  })

  it('resets to page 1, so a narrowed filter cannot strand the user', () => {
    expect(
      applyFilterChange({ company_id: 'c1', page: 7 }, { status: 'failed' })
        .page,
    ).toBeUndefined()
  })

  it('clears a filter when the change sets it undefined', () => {
    expect(
      applyFilterChange({ company_id: 'c1' }, { company_id: undefined })
        .company_id,
    ).toBeUndefined()
  })

  it('closes the panel when a filter changes', () => {
    const next = applyFilterChange(
      { voucher: '4821', entry: 'e1', tab: 'details' },
      { company_id: 'c2' },
    )
    expect(next.voucher).toBeUndefined()
    expect(next.entry).toBeUndefined()
    expect(next.tab).toBeUndefined()
  })
})

describe('applyVoucherSelection', () => {
  it('opens the voucher on the tab the caller asked for', () => {
    const next = applyVoucherSelection(
      { tab: 'details' },
      { voucher: 'V-1', entry: 'e1', tab: 'lines' },
    )
    expect(next).toMatchObject({ voucher: 'V-1', entry: 'e1', tab: 'lines' })
  })

  it('keeps the tab in view when the caller names none', () => {
    expect(
      applyVoucherSelection({ tab: 'activity' }, { voucher: 'V-2' }).tab,
    ).toBe('activity')
  })

  it('keeps the filters the selection says nothing about', () => {
    const next = applyVoucherSelection(
      { company_id: 'c1', page: 3 },
      { voucher: 'V-1' },
    )
    expect(next).toMatchObject({ company_id: 'c1', page: 3 })
  })

  it('clears the tab when the panel closes, so the URL keeps no dead state', () => {
    const next = applyVoucherSelection({ voucher: 'V-1', tab: 'lines' }, {})
    expect(next.voucher).toBeUndefined()
    expect(next.entry).toBeUndefined()
    expect(next.tab).toBeUndefined()
  })
})

describe('listableEntryTypes', () => {
  it('drops the types no listing can return', () => {
    expect(
      listableEntryTypes(['purchase_invoice', 'payment', 'credit_note']),
    ).toEqual(['credit_note', 'purchase_invoice'])
  })

  it('keeps credit notes and journal entries, which move real spend', () => {
    expect(listableEntryTypes(['journal_entry', 'credit_note'])).toEqual([
      'credit_note',
      'journal_entry',
    ])
  })

  it('deduplicates and sorts, since the summary reports one row per currency', () => {
    expect(
      listableEntryTypes([
        'purchase_invoice',
        'purchase_invoice',
        'credit_note',
      ]),
    ).toEqual(['credit_note', 'purchase_invoice'])
  })
})

describe('applySortChange', () => {
  it('sorts from the first page, keeping the filters', () => {
    expect(
      applySortChange(
        { company_id: 'c1', page: 4 },
        { sort: 'amount', order: 'desc' },
      ),
    ).toEqual({
      company_id: 'c1',
      sort: 'amount',
      order: 'desc',
      page: undefined,
    })
  })

  it('leaves an open voucher open', () => {
    const next = applySortChange(
      { voucher: '4821', tab: 'lines' },
      { sort: 'vendor_name', order: 'asc' },
    )
    expect(next).toMatchObject({ voucher: '4821', tab: 'lines' })
  })
})

describe('applyFilterChange and the sort', () => {
  it('keeps the sort when a filter changes', () => {
    expect(
      applyFilterChange({ sort: 'amount', order: 'asc' }, { company_id: 'c1' }),
    ).toMatchObject({ sort: 'amount', order: 'asc', company_id: 'c1' })
  })
})

describe('defaultVoucherOrder', () => {
  it('starts suppliers A–Z and figures and dates largest first', () => {
    expect(defaultVoucherOrder('vendor_name')).toBe('asc')
    expect(defaultVoucherOrder('amount')).toBe('desc')
    expect(defaultVoucherOrder('accounting_date')).toBe('desc')
    expect(defaultVoucherOrder('voucher_number')).toBe('desc')
  })
})

describe('resolveVoucherSort', () => {
  it('lists the newest vouchers first when the URL names no sort', () => {
    expect(resolveVoucherSort({}, true)).toEqual({
      sort: 'accounting_date',
      order: 'desc',
    })
  })

  it('starts a chosen column in its own order', () => {
    expect(resolveVoucherSort({ sort: 'vendor_name' }, true)).toEqual({
      sort: 'vendor_name',
      order: 'asc',
    })
  })

  it('keeps the order the URL asks for', () => {
    expect(resolveVoucherSort({ sort: 'amount', order: 'asc' }, true)).toEqual({
      sort: 'amount',
      order: 'asc',
    })
  })

  it('falls back to newest first when amounts are in different currencies', () => {
    expect(resolveVoucherSort({ sort: 'amount', order: 'asc' }, false)).toEqual(
      { sort: 'accounting_date', order: 'desc' },
    )
  })
})
