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
  AgreementRead,
  AgreementReport,
  AgreementSummaryRead,
  FindingRead,
  TermRead,
} from '#/lib/api/agreement-types'
import { AgreementHeading } from './detail/agreement-heading'
import { AgreementsPanel } from './list/agreements-panel'
import { ReportTab } from './report/report-tab'
import { TermCard } from './terms/term-card'

vi.mock('@tanstack/react-router', async (importOriginal) => {
  const actual = await importOriginal<typeof RouterModule>()
  return {
    ...actual,
    Link: ({
      to,
      children,
      search,
      params,
      ...props
    }: {
      to: string
      children?: ReactNode
      search?: Record<string, string>
      params?: Record<string, string>
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

const SUMMARY: AgreementSummaryRead = {
  id: 'a1',
  company_id: 'c1',
  title: 'Atea framework 2026',
  reference: 'FA-2026-17',
  supplier: { vendor_id: 'v1', name: 'Atea A/S' },
  supplier_name: 'Atea A/S',
  starts_on: '2026-01-01',
  ends_on: '2027-12-31',
  currency: 'DKK',
  status: 'active',
  expired: false,
  read_error: null,
  analysed_at: '2026-09-27T10:00:00Z',
  created_at: '2026-09-20T10:00:00Z',
  open_rule_breaks: 3,
  rule_break_amount: '21400',
  base_currency: 'DKK',
}

const AGREEMENT: AgreementRead = {
  ...SUMMARY,
  supplier_vat_number: 'DK12345678',
  supplier_website: null,
  summary: null,
  read_at: '2026-09-20T10:05:00Z',
  file: { filename: 'atea.pdf', file_size: 1000 },
  terms: [],
}

const TERM: TermRead = {
  id: 't1',
  agreement_id: 'a1',
  kind: 'preferred_supplier',
  status: 'draft',
  source: 'ai',
  scope: 'IT equipment',
  conditions: 'when available from stock',
  item: null,
  unit: null,
  unit_price: null,
  discount_percent: null,
  commitment_amount: null,
  commitment_period: null,
  tiers: null,
  currency: 'DKK',
  scope_category_ids: [],
  quotes: [
    {
      text: 'IT equipment shall be purchased from Atea when available from stock.',
      page: 3,
    },
  ],
  confidence: '0.9',
  created_at: '2026-09-20T10:05:00Z',
  updated_at: null,
}

const FINDING: FindingRead = {
  id: 'f1',
  agreement_id: 'a1',
  term_id: 't1',
  term_kind: 'preferred_supplier',
  term_scope: 'IT equipment',
  term_conditions: 'when available from stock',
  kind: 'off_contract',
  severity: 'rule_break',
  amount: '9200',
  line_amount: '9200',
  currency: 'DKK',
  expected: null,
  actual: null,
  quantity: '1',
  reason:
    'IT equipment should be bought from Atea A/S (when available from stock), but was bought from Proshop A/S.',
  judge_confidence: '0.9',
  spent_on: '2026-03-01',
  invoice_line_id: 'l1',
  invoice_id: 'i1',
  voucher_id: '4821',
  item: 'Dell Latitude 5450',
  supplier_name: 'Proshop A/S',
  from_supplier: false,
  review_status: 'open',
  review_note: null,
  reviewed_by_name: null,
  reviewed_at: null,
}

const REPORT: AgreementReport = {
  agreement_id: 'a1',
  analysed_at: '2026-09-27T10:00:00Z',
  currency: 'DKK',
  in_scope_spend: '50000',
  supplier_spend: '40000',
  totals: [
    { kind: 'off_contract', severity: 'rule_break', count: 1, amount: '9200' },
    { kind: 'potential_saving', severity: 'info', count: 2, amount: '800' },
  ],
  commitments: [],
  findings: { items: [FINDING], page: 1, page_size: 50, total: 1 },
}

describe('AgreementsPanel', () => {
  it('lists agreements with their open rule breaks', () => {
    render(
      <AgreementsPanel
        agreements={[
          SUMMARY,
          {
            ...SUMMARY,
            id: 'a2',
            title: 'Office supplies',
            status: 'review',
            open_rule_breaks: 0,
          },
        ]}
        error={false}
        onRetry={vi.fn()}
        upload={null}
      />,
    )

    const list = within(screen.getByRole('region', { name: 'Agreements list' }))
    expect(
      list
        .getByRole('link', { name: 'Atea framework 2026' })
        .getAttribute('href'),
    ).toBe('/agreements/a1')
    expect(list.getByText('Needs review')).toBeTruthy()
    expect(screen.getByText(/3 rule breaks are open/)).toBeTruthy()
    expect(
      screen.queryByRole('region', { name: 'Upload an agreement' }),
    ).toBeNull()
  })

  it('uploads a dropped PDF for a manager', async () => {
    const onUpload = vi.fn(async () => {})
    render(
      <AgreementsPanel
        agreements={[]}
        error={false}
        onRetry={vi.fn()}
        upload={{ companies: [{ id: 'c1', name: 'Acme' }], onUpload }}
      />,
    )
    const file = new File(['%PDF'], 'atea.pdf', { type: 'application/pdf' })

    fireEvent.change(screen.getByLabelText('Agreement file'), {
      target: { files: [file] },
    })
    fireEvent.click(screen.getByRole('button', { name: /Upload and read/ }))

    await waitFor(() => {
      expect(onUpload).toHaveBeenCalledWith('c1', file, expect.any(Function))
    })
  })

  it('uploads for the only company once the companies have loaded', async () => {
    const onUpload = vi.fn(async () => {})
    const panel = (companies: Array<{ id: string; name: string }>) => (
      <AgreementsPanel
        agreements={[]}
        error={false}
        onRetry={vi.fn()}
        upload={{ companies, onUpload }}
      />
    )
    const { rerender } = render(panel([]))
    rerender(panel([{ id: 'c1', name: 'Acme' }]))
    const file = new File(['%PDF'], 'atea.pdf', { type: 'application/pdf' })

    fireEvent.change(screen.getByLabelText('Agreement file'), {
      target: { files: [file] },
    })
    fireEvent.click(screen.getByRole('button', { name: /Upload and read/ }))

    await waitFor(() => {
      expect(onUpload).toHaveBeenCalledWith('c1', file, expect.any(Function))
    })
  })

  it('refuses a file that is not a PDF', () => {
    render(
      <AgreementsPanel
        agreements={[]}
        error={false}
        onRetry={vi.fn()}
        upload={{ companies: [{ id: 'c1', name: 'Acme' }], onUpload: vi.fn() }}
      />,
    )

    fireEvent.change(screen.getByLabelText('Agreement file'), {
      target: { files: [new File(['x'], 'terms.docx')] },
    })

    expect(screen.getByRole('alert').textContent).toContain('terms.docx')
  })

  it('offers a retry when the list fails', () => {
    const onRetry = vi.fn()
    render(
      <AgreementsPanel
        agreements={undefined}
        error
        onRetry={onRetry}
        upload={null}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(onRetry).toHaveBeenCalled()
  })
})

describe('AgreementHeading', () => {
  function heading(overrides: Partial<AgreementRead>, canEdit = true) {
    const onReadAgain = vi.fn(async () => {})
    render(
      <AgreementHeading
        agreement={{ ...AGREEMENT, ...overrides }}
        canEdit={canEdit}
        onDelete={vi.fn(async () => {})}
        onReadAgain={onReadAgain}
      />,
    )
    return onReadAgain
  }

  it('reads an agreement again once the manager confirms', async () => {
    const onReadAgain = heading({ status: 'review' })

    fireEvent.click(screen.getByRole('button', { name: /Read again/ }))
    const dialog = screen.getByRole('alertdialog')
    expect(dialog.textContent).toContain('confirmed or rejected are')
    fireEvent.click(within(dialog).getByRole('button', { name: 'Read again' }))

    await waitFor(() => {
      expect(onReadAgain).toHaveBeenCalledOnce()
    })
  })

  it('offers no re-read while the agreement is being read', () => {
    heading({ status: 'reading' })

    expect(screen.queryByRole('button', { name: /Read again/ })).toBeNull()
  })

  it('offers a viewer neither a re-read nor a delete', () => {
    heading({ status: 'active' }, false)

    expect(screen.queryByRole('button', { name: /Read again/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /Delete/ })).toBeNull()
  })
})

describe('TermCard', () => {
  it('confirms a draft and jumps to the quoted page', async () => {
    const onUpdate = vi.fn(async () => {})
    const onShowPage = vi.fn()
    render(
      <TermCard
        term={TERM}
        canEdit
        busy={false}
        onUpdate={onUpdate}
        onShowPage={onShowPage}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: /p\. 3/ }))
    expect(onShowPage).toHaveBeenCalledWith(3)
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }))
    await waitFor(() => {
      expect(onUpdate).toHaveBeenCalledWith({ status: 'confirmed' })
    })
  })

  it('edits a term and saves it confirmed', async () => {
    const onUpdate = vi.fn(async () => {})
    render(
      <TermCard
        term={TERM}
        canEdit
        busy={false}
        onUpdate={onUpdate}
        onShowPage={vi.fn()}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Edit' }))
    fireEvent.change(screen.getByDisplayValue('IT equipment'), {
      target: { value: 'IT equipment and peripherals' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Save and confirm' }))

    await waitFor(() => {
      expect(onUpdate).toHaveBeenCalledWith(
        expect.objectContaining({
          scope: 'IT equipment and peripherals',
          conditions: 'when available from stock',
          status: 'confirmed',
        }),
      )
    })
  })

  it('picks the currency of an agreed price from the currency list', async () => {
    const onUpdate = vi.fn(async () => {})
    render(
      <TermCard
        term={{
          ...TERM,
          kind: 'agreed_price',
          scope: 'Lenovo ThinkPad T14 Gen 5',
          item: 'Lenovo ThinkPad T14 Gen 5',
          unit: 'piece',
          unit_price: '8000',
        }}
        canEdit
        busy={false}
        onUpdate={onUpdate}
        onShowPage={vi.fn()}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Edit' }))
    const currency = screen.getByRole<HTMLInputElement>('combobox', {
      name: 'Currency',
    })
    expect(currency.value).toContain('DKK')
    fireEvent.click(currency)
    fireEvent.change(currency, { target: { value: 'euro' } })
    fireEvent.click(await screen.findByRole('option', { name: /^EUR/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Save and confirm' }))

    await waitFor(() => {
      expect(onUpdate).toHaveBeenCalledWith(
        expect.objectContaining({ currency: 'EUR', status: 'confirmed' }),
      )
    })
  })

  it('shows the error when a change is refused', async () => {
    render(
      <TermCard
        term={TERM}
        canEdit
        busy={false}
        onUpdate={vi.fn(async () => {
          throw new Error('Insufficient permissions')
        })}
        onShowPage={vi.fn()}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Reject' }))

    expect(await screen.findByText('Insufficient permissions')).toBeTruthy()
  })

  it('offers a viewer no controls', () => {
    render(
      <TermCard
        term={TERM}
        canEdit={false}
        busy={false}
        onUpdate={vi.fn()}
        onShowPage={vi.fn()}
      />,
    )

    expect(screen.queryByRole('button', { name: 'Confirm' })).toBeNull()
  })
})

describe('ReportTab', () => {
  function renderReport(
    overrides: Partial<Parameters<typeof ReportTab>[0]> = {},
  ) {
    const props = {
      agreement: AGREEMENT,
      report: REPORT,
      error: false,
      onRetry: vi.fn(),
      view: 'open' as const,
      onViewChange: vi.fn(),
      canEdit: true,
      analysing: false,
      onAnalyse: vi.fn(),
      onReview: vi.fn(async () => {}),
      ...overrides,
    }
    render(<ReportTab {...props} />)
    return props
  }

  it('leads with the open rule breaks and the spend in scope', () => {
    renderReport()

    expect(
      within(
        screen.getByRole('region', { name: 'Open rule breaks' }),
      ).getByText('1'),
    ).toBeTruthy()
    expect(
      screen.getByRole('region', { name: 'Spend in scope' }).textContent,
    ).toContain('80% with the supplier')
    const findings = within(screen.getByRole('region', { name: 'Findings' }))
    expect(findings.getByText('Off-contract purchase')).toBeTruthy()
    expect(findings.getByText('Dell Latitude 5450')).toBeTruthy()
    expect(
      findings
        .getByRole('link', { name: /Open the voucher/ })
        .getAttribute('href'),
    ).toBe('/invoice-lines?company_id=c1&voucher=4821&tab=lines')
  })

  it('accepts a finding as an exception with a note', async () => {
    const props = renderReport()

    fireEvent.click(screen.getByRole('button', { name: 'Review' }))
    fireEvent.change(await screen.findByLabelText('Note'), {
      target: { value: 'Atea out of stock' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Accept as exception' }))

    await waitFor(() => {
      expect(props.onReview).toHaveBeenCalledWith('f1', {
        review_status: 'exception',
        note: 'Atea out of stock',
      })
    })
  })

  it('shows every finding on one purchase under its item', () => {
    const saving: FindingRead = {
      ...FINDING,
      id: 'f2',
      term_id: 't2',
      term_kind: 'agreed_price',
      kind: 'potential_saving',
      severity: 'info',
      amount: '1200',
      reason:
        'Bought from Proshop A/S at 9,200.00 against the agreed 8,000.00 DKK.',
    }
    renderReport({
      report: {
        ...REPORT,
        findings: { ...REPORT.findings, items: [FINDING, saving], total: 2 },
      },
    })

    const findings = within(screen.getByRole('region', { name: 'Findings' }))
    expect(findings.getAllByText('Dell Latitude 5450')).toHaveLength(1)
    expect(findings.getByText('Off-contract purchase')).toBeTruthy()
    expect(findings.getByText('Potential saving')).toBeTruthy()
    expect(findings.getAllByRole('button', { name: 'Review' })).toHaveLength(2)
  })

  it('shows a long reason in full on request', () => {
    const reason = `${FINDING.reason} ${'The item is a laptop, which is IT equipment. '.repeat(4)}`
    renderReport({
      report: {
        ...REPORT,
        findings: {
          ...REPORT.findings,
          items: [{ ...FINDING, reason }],
        },
      },
    })

    const more = screen.getByRole('button', { name: 'Show more' })
    expect(more.getAttribute('aria-expanded')).toBe('false')
    fireEvent.click(more)

    expect(
      screen
        .getByRole('button', { name: 'Show less' })
        .getAttribute('aria-expanded'),
    ).toBe('true')
  })

  it('says the report waits for a confirmed agreement', () => {
    renderReport({ agreement: { ...AGREEMENT, status: 'review' } })

    expect(screen.getByText(/The report starts once/)).toBeTruthy()
  })

  it('checks again on request', () => {
    const props = renderReport()

    fireEvent.click(screen.getByRole('button', { name: /Check again/ }))
    expect(props.onAnalyse).toHaveBeenCalled()
  })
})
