import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'
import { PriceBenchmarkCard } from './price-benchmark-card'

afterEach(() => {
  cleanup()
})

describe('PriceBenchmarkCard', () => {
  it('lets an admin opt the organization out', async () => {
    const onChange = vi.fn(async () => {})
    render(<PriceBenchmarkCard enabled canManage onChange={onChange} />)

    fireEvent.click(
      screen.getByRole('switch', { name: 'Take part in the price benchmark' }),
    )

    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith(false)
    })
  })

  it('says what opting out means and who may change it', () => {
    render(
      <PriceBenchmarkCard
        enabled={false}
        canManage={false}
        onChange={vi.fn()}
      />,
    )

    expect(screen.getByText(/your items get no alternatives/)).toBeTruthy()
    expect(
      screen.getByText('Only an organization admin can change this.'),
    ).toBeTruthy()
    expect(
      screen
        .getByRole('switch', { name: 'Take part in the price benchmark' })
        .hasAttribute('data-disabled'),
    ).toBe(true)
  })
})
