import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'
import type { EmissionsSummaryRead } from '#/lib/api/emission-types'
import type { InvoiceLineRead, VoucherGroupRead } from '#/lib/api/types'
import { EmissionsCard } from './emissions-card'
import { LineEmissions, LineSector } from './line-emissions'
import { LineEmissionsPanel } from './line-emissions-panel'
import { EmissionSectorField } from './sector-field'
import type { SectorSearch } from './sector-field'
import { VoucherEmissions } from './voucher-emissions'

afterEach(() => {
  cleanup()
})

const FACTOR_SET = {
  source: 'open_ceda',
  version: 'CEDA 2025',
  currency: 'USD',
  price_year: 2023,
  price_basis: 'purchaser',
  attribution: 'CEDA by Watershed',
}

function summary(
  overrides: Partial<EmissionsSummaryRead> = {},
): EmissionsSummaryRead {
  return {
    factor_set: FACTOR_SET,
    kg_co2e: '12437',
    spend: [{ currency: 'DKK', posted_spend: '1000', estimated_spend: '870' }],
    vouchers_by_status: { estimated: 8, partial: 1, no_lines: 2 },
    ...overrides,
  }
}

const HOSTING = { id: 's1', code: '518200', name: 'Data processing, hosting' }

function line(overrides: Partial<InvoiceLineRead> = {}): InvoiceLineRead {
  return {
    id: 'l1',
    invoice_id: 'i1',
    company_id: 'c1',
    item_name: 'Dedicated server',
    description: null,
    quantity: null,
    unit: null,
    unit_price: null,
    amount: '100',
    native_account_code: null,
    origin: 'document_ai',
    sequence: 0,
    currency: 'DKK',
    base_currency: 'DKK',
    base_amount: '100',
    fx_rate: null,
    fx_rate_date: null,
    status: 'ai_categorized',
    level_1: null,
    level_2: null,
    level_3: null,
    level_4: null,
    account_code: null,
    account_name: null,
    confidence: null,
    rationale: null,
    spend_category_id: null,
    category_stale: false,
    needs_review: false,
    verified_fields: [],
    ...overrides,
  }
}

function group(overrides: Partial<VoucherGroupRead>): VoucherGroupRead {
  return {
    voucher_id: '4821',
    company_id: 'c1',
    accounting_date: '2026-09-03',
    entry_types: ['purchase_invoice'],
    entry_count: 1,
    amount: '100',
    debit_total: '100',
    credit_total: '0',
    currency: 'DKK',
    vendor_id: null,
    vendor_name: null,
    unconverted_count: 0,
    entries: [],
    lines: [],
    doc_status: null,
    doc_error: null,
    invoice_number: null,
    document_invoice_number: null,
    totals_agree: null,
    document_total: null,
    invoice_total: null,
    invoice_currency: null,
    ...overrides,
  }
}

describe('EmissionsCard', () => {
  it('shows the total in tonnes, the method, the attribution and the share estimated', () => {
    render(
      <EmissionsCard summary={summary()} error={false} onRetry={vi.fn()} />,
    )

    expect(screen.getByText('12.4 t CO₂e')).toBeTruthy()
    expect(
      screen.getByText('Spend-based estimate · CEDA 2025 · 2023 USD'),
    ).toBeTruthy()
    expect(screen.getByText('CEDA by Watershed')).toBeTruthy()
    expect(screen.getByText('87%')).toBeTruthy()
  })

  it('counts the vouchers not estimated, with their reasons', () => {
    render(
      <EmissionsCard summary={summary()} error={false} onRetry={vi.fn()} />,
    )

    const card = screen.getByRole('region', { name: 'Vouchers not estimated' })
    expect(card.textContent).toContain('2')
    expect(card.textContent).toContain(
      'the voucher has no invoice lines to estimate from',
    )
    expect(card.textContent).toContain('1 estimated from only some')
  })

  it('says no factors are imported instead of showing a figure', () => {
    render(
      <EmissionsCard
        summary={summary({ factor_set: null, kg_co2e: null })}
        error={false}
        onRetry={vi.fn()}
      />,
    )

    expect(screen.getByText(/No emission factors are imported/)).toBeTruthy()
    expect(screen.queryByText(/CO₂e/)).toBeNull()
  })

  it('holds its place while loading and offers a retry when it fails', () => {
    const onRetry = vi.fn()
    const { rerender } = render(
      <EmissionsCard summary={undefined} error={false} onRetry={onRetry} />,
    )
    expect(screen.getByTestId('emissions-loading')).toBeTruthy()

    rerender(
      <EmissionsCard summary={undefined} error={true} onRetry={onRetry} />,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(onRetry).toHaveBeenCalled()
  })
})

describe('VoucherEmissions', () => {
  it('shows an estimated voucher’s emissions', () => {
    render(
      <VoucherEmissions
        group={group({ kg_co2e: '72.500', emissions_status: 'estimated' })}
      />,
    )

    expect(screen.getByText('72.5 kg CO₂e')).toBeTruthy()
  })

  it('marks a partial estimate and says why', () => {
    render(
      <VoucherEmissions
        group={group({ kg_co2e: '5.8', emissions_status: 'partial' })}
      />,
    )

    expect(
      screen.getByLabelText(/5\.8 kg CO₂e\*\. Estimated from some lines/),
    ).toBeTruthy()
  })

  it('gives the reason there is no estimate', () => {
    render(
      <VoucherEmissions
        group={group({ kg_co2e: null, emissions_status: 'no_lines' })}
      />,
    )

    expect(screen.getByLabelText(/has no invoice lines/)).toBeTruthy()
  })
})

describe('LineSector and LineEmissions', () => {
  it('names the AI’s sector, flags an unsure one, and explains it on focus', () => {
    render(
      <LineSector
        line={line({
          emission_sector: HOSTING,
          emission_sector_source: 'ai',
          emission_sector_confidence: '0.4',
          emission_sector_rationale: 'A rented server.',
          emission_needs_review: true,
          emission_area: 'DE',
        })}
      />,
    )

    expect(screen.getByText('Data processing, hosting')).toBeTruthy()
    expect(screen.getByText('AI')).toBeTruthy()
    expect(screen.getByText('Check sector')).toBeTruthy()
    expect(
      screen.getByLabelText(
        'Emission sector: 518200 Data processing, hosting. Matched by AI (40% sure). A rented server. Factor for DE.',
      ),
    ).toBeTruthy()
  })

  it('marks a person’s choice as theirs', () => {
    render(
      <LineSector
        line={line({
          emission_sector: HOSTING,
          emission_sector_source: 'human',
        })}
      />,
    )

    expect(screen.getByText('person')).toBeTruthy()
    expect(screen.getByLabelText(/Chosen by a person/)).toBeTruthy()
  })

  it('shows nothing for a line without a sector, and a dash for no emissions', () => {
    const { container } = render(<LineSector line={line()} />)
    expect(container.textContent).toBe('')

    render(<LineEmissions line={line({ kg_co2e: null })} />)
    expect(screen.getByText('—')).toBeTruthy()
  })
})

function search(overrides: Partial<SectorSearch> = {}): SectorSearch {
  return {
    available: true,
    sectors: [HOSTING],
    onSearch: vi.fn(),
    ...overrides,
  }
}

describe('EmissionSectorField', () => {
  it('searches as the reviewer types and saves the sector picked', async () => {
    const onChoose = vi.fn().mockResolvedValue(undefined)
    const sectors = search()
    render(
      <EmissionSectorField
        line={line()}
        search={sectors}
        onChoose={onChoose}
      />,
    )

    const picker = screen.getByRole('combobox', { name: 'Emission sector' })
    fireEvent.click(picker)
    fireEvent.change(picker, { target: { value: 'host' } })
    expect(sectors.onSearch).toHaveBeenCalledWith('host')
    fireEvent.click(
      await screen.findByRole('option', { name: 'Data processing, hosting' }),
    )

    await waitFor(() => expect(onChoose).toHaveBeenCalledWith('s1'))
  })

  it('clears a chosen sector', async () => {
    const onChoose = vi.fn().mockResolvedValue(undefined)
    render(
      <EmissionSectorField
        line={line({ emission_sector: HOSTING, emission_sector_source: 'ai' })}
        search={search()}
        onChoose={onChoose}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Clear' }))

    await waitFor(() => expect(onChoose).toHaveBeenCalledWith(null))
  })

  it('shows why no sector can be chosen when no factors are imported', () => {
    render(
      <EmissionSectorField
        line={line()}
        search={search({ available: false })}
        onChoose={vi.fn()}
      />,
    )

    expect(screen.getByText(/No emission factors are imported/)).toBeTruthy()
    expect(screen.queryByRole('combobox')).toBeNull()
  })

  it('shows a refused choice as an error', async () => {
    const onChoose = vi.fn().mockRejectedValue(new Error('Not offered'))
    render(
      <EmissionSectorField
        line={line({ emission_sector: HOSTING, emission_sector_source: 'ai' })}
        search={search()}
        onChoose={onChoose}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Clear' }))

    expect(await screen.findByText('Not offered')).toBeTruthy()
  })
})

const CALCULATION = {
  spend: '1000.00',
  currency: 'DKK',
  rate: '0.145',
  rate_date: '2025-07-01',
  converted: '145.00',
  factor: '0.5',
  factor_currency: 'USD',
  factor_area: 'DE',
  sector: HOSTING,
  kg_co2e: '72.500',
}

describe('LineEmissionsPanel', () => {
  it('shows the sector, the AI’s reasoning and the calculation', () => {
    render(
      <LineEmissionsPanel
        line={line({
          emission_sector: HOSTING,
          emission_sector_source: 'ai',
          emission_sector_confidence: '0.4',
          emission_sector_rationale: 'A rented server is hosting.',
          emission_needs_review: true,
          kg_co2e: '72.500',
          emission_calculation: CALCULATION,
        })}
      />,
    )

    const panel = screen.getByRole('region', { name: 'Emissions' })
    expect(panel.textContent).toContain('Data processing, hosting')
    expect(panel.textContent).toContain('Matched by AI · 40% sure')
    expect(panel.textContent).toContain('A rented server is hosting.')
    expect(panel.textContent).toContain('0.145 DKK→USD on 1 Jul 2025')
    expect(panel.textContent).toContain('× 0.5 kg CO₂e per USD')
    expect(panel.textContent).toContain('factor for DE')
    expect(screen.getByText('72.5 kg CO₂e')).toBeTruthy()
  })

  it('says a line with a sector but no calculation was not estimated, and why it might be', () => {
    render(
      <LineEmissionsPanel
        line={line({
          emission_sector: HOSTING,
          emission_sector_source: 'human',
        })}
      />,
    )

    expect(screen.getByText('Chosen by a person.')).toBeTruthy()
    expect(screen.getByText(/Not estimated/)).toBeTruthy()
  })

  it('says when a line has no sector yet', () => {
    render(<LineEmissionsPanel line={line()} />)

    expect(screen.getByText(/No emission sector yet/)).toBeTruthy()
  })
})

describe('LineEmissions calculation', () => {
  it('reads out the calculation on focus', () => {
    render(
      <LineEmissions
        line={line({ kg_co2e: '72.500', emission_calculation: CALCULATION })}
      />,
    )

    expect(
      screen.getByLabelText(/72\.5 kg CO₂e: Share of the voucher’s spend/),
    ).toBeTruthy()
  })
})
