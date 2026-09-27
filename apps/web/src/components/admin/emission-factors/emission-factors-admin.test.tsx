import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'
import type {
  AdminFactorSetRead,
  EmissionFactorsStatusRead,
  ReferenceImportRead,
} from '#/lib/api/admin-emission-factor-types'
import { ActivateDialog } from './activate-dialog'
import { EmissionFactorsAdmin } from './emission-factors-admin'
import type { EmissionFactorsAdminProps } from './emission-factors-admin'
import { workbookProblem } from './workbook-upload'

afterEach(() => {
  cleanup()
})

const CEDA_2025: AdminFactorSetRead = {
  id: 'set-2025',
  source: 'open_ceda',
  version: 'CEDA 2025',
  classification: 'ceda-bea',
  currency: 'USD',
  price_year: 2023,
  price_basis: 'purchaser',
  attribution: 'CEDA by Watershed',
  sectors: 400,
  factors: 68000,
  imported_at: '2026-09-27T10:00:00Z',
  active: true,
}

const CEDA_2024: AdminFactorSetRead = {
  ...CEDA_2025,
  id: 'set-2024',
  version: 'CEDA 2024',
  price_year: 2022,
  active: false,
}

const STATUS: EmissionFactorsStatusRead = {
  sets: [CEDA_2025, CEDA_2024],
  price_indices: [
    {
      series: 'CPIAUCSL',
      label: 'US CPI',
      currency: 'USD',
      months: 956,
      latest_month: '2026-08-01',
      base_year: 2023,
      base_average: '304.7025',
    },
  ],
  coverage: [
    {
      company_id: 'c1',
      company_name: 'VectorLab ApS',
      organization_name: 'VectorLab',
      lines: 80,
      ai: 70,
      human: 2,
      needs_review: 3,
      unmatched: 8,
    },
  ],
}

const FINISHED_JOB: ReferenceImportRead = {
  id: 'j1',
  kind: 'factor_workbook',
  status: 'succeeded',
  subject: 'Open CEDA 2025 by Watershed.xlsx',
  activate: true,
  requested_by: 'u1',
  requested_by_name: 'Hadi',
  requested_at: '2026-09-27T10:00:00Z',
  started_at: '2026-09-27T10:00:01Z',
  finished_at: '2026-09-27T10:00:41Z',
  result: { version: 'CEDA 2025', sectors: 400, factors: 68000, active: true },
  error: null,
}

function renderPage(overrides: Partial<EmissionFactorsAdminProps> = {}) {
  const props: EmissionFactorsAdminProps = {
    status: STATUS,
    statusError: false,
    onRetry: vi.fn(),
    jobs: [],
    refreshing: false,
    refreshError: null,
    importingWorkbook: false,
    matchRequests: {},
    onActivate: vi.fn(),
    onRefresh: vi.fn(),
    onUpload: vi.fn(async () => {}),
    onMatch: vi.fn(),
    ...overrides,
  }
  render(<EmissionFactorsAdmin {...props} />)
  return props
}

describe('EmissionFactorsAdmin', () => {
  it('lists the sets with the active one marked, and offers to activate the others', () => {
    const props = renderPage()

    const sets = screen.getByRole('region', { name: 'Factor sets' })
    expect(sets.textContent).toContain('CEDA 2025')
    expect(sets.textContent).toContain('Active')
    expect(sets.textContent).toContain('68,000')
    fireEvent.click(screen.getByRole('button', { name: 'Activate' }))
    expect(props.onActivate).toHaveBeenCalledWith(CEDA_2024)
  })

  it('shows the price index and refreshes it', () => {
    const props = renderPage()

    const card = screen.getByRole('region', { name: 'Price index' })
    expect(card.textContent).toContain('Aug 2026')
    expect(card.textContent).toContain('304.70')
    fireEvent.click(screen.getByRole('button', { name: 'Refresh from FRED' }))
    expect(props.onRefresh).toHaveBeenCalledWith('CPIAUCSL')
  })

  it('says estimates are unadjusted while the index is not imported', () => {
    renderPage({
      status: {
        ...STATUS,
        price_indices: [
          {
            ...STATUS.price_indices[0],
            months: 0,
            latest_month: null,
            base_average: null,
          },
        ],
      },
    })

    expect(
      screen.getByText(
        'Not imported, so estimates are not adjusted for inflation.',
      ),
    ).toBeTruthy()
  })

  it('disables the refresh while one is running', () => {
    renderPage({ refreshing: true })

    const button = screen.getByRole('button', { name: /Refreshing/ })
    expect((button as HTMLButtonElement).disabled).toBe(true)
  })

  it('uploads a workbook with the activate choice', async () => {
    const props = renderPage()
    const file = new File(['PK'], 'Open CEDA 2026.xlsx')

    fireEvent.change(screen.getByLabelText('Workbook file'), {
      target: { files: [file] },
    })
    fireEvent.click(screen.getByRole('button', { name: /Upload and import/ }))

    await waitFor(() => {
      expect(props.onUpload).toHaveBeenCalledWith(
        file,
        true,
        expect.any(Function),
      )
    })
  })

  it('refuses a file that is not a workbook before uploading', () => {
    const props = renderPage()

    fireEvent.change(screen.getByLabelText('Workbook file'), {
      target: { files: [new File(['%PDF'], 'invoice.pdf')] },
    })

    expect(
      screen.getByText('invoice.pdf is not an .xlsx workbook.'),
    ).toBeTruthy()
    const button = screen.getByRole('button', { name: /Upload and import/ })
    expect((button as HTMLButtonElement).disabled).toBe(true)
    expect(props.onUpload).not.toHaveBeenCalled()
  })

  it('shows the server’s refusal of an upload', async () => {
    renderPage({
      onUpload: vi.fn(async () => {
        throw new Error('An import of this kind is already queued or running')
      }),
    })

    fireEvent.change(screen.getByLabelText('Workbook file'), {
      target: { files: [new File(['PK'], 'ceda.xlsx')] },
    })
    fireEvent.click(screen.getByRole('button', { name: /Upload and import/ }))

    expect(
      await screen.findByText(
        'An import of this kind is already queued or running',
      ),
    ).toBeTruthy()
  })

  it('lists the jobs with their outcome', () => {
    renderPage({
      jobs: [
        FINISHED_JOB,
        {
          ...FINISHED_JOB,
          id: 'j2',
          kind: 'price_index',
          subject: 'CPIAUCSL',
          status: 'failed',
          result: null,
          error: 'downloading CPIAUCSL: timed out',
        },
      ],
    })

    const jobs = screen.getByRole('region', { name: 'Recent imports' })
    expect(jobs.textContent).toContain(
      'CEDA 2025: 400 sectors, 68,000 factors, active',
    )
    expect(jobs.textContent).toContain('took 40 s')
    expect(jobs.textContent).toContain('downloading CPIAUCSL: timed out')
  })

  it('shows each company’s coverage and asks for matching', () => {
    const props = renderPage({
      matchRequests: { c1: { state: 'requested' } },
    })

    const coverage = screen.getByRole('region', { name: 'Sector coverage' })
    expect(coverage.textContent).toContain('VectorLab ApS')
    expect(screen.getByLabelText('VectorLab ApS: 90% matched')).toBeTruthy()
    expect(coverage.textContent).toContain('Matching requested')
    fireEvent.click(
      screen.getByRole('button', { name: /Match emission sectors/ }),
    )
    expect(props.onMatch).toHaveBeenCalledWith('c1')
  })

  it('offers a retry when the status fails to load', () => {
    const props = renderPage({ status: undefined, statusError: true })

    fireEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(props.onRetry).toHaveBeenCalled()
  })
})

describe('ActivateDialog', () => {
  it('names both sets and warns when lines need matching again', () => {
    render(
      <ActivateDialog
        target={{ ...CEDA_2024, classification: 'exiobase' }}
        current={CEDA_2025}
        busy={false}
        error={null}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
      />,
    )

    const text = screen.getByRole('alertdialog').textContent
    expect(text).toContain('CEDA 2025 is active now.')
    expect(text).toContain('every line will need matching')
  })
})

describe('workbookProblem', () => {
  it('accepts an .xlsx within the limit', () => {
    expect(workbookProblem(new File(['PK'], 'ceda.XLSX'))).toBeNull()
  })
})
