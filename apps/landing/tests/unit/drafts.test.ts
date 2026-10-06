import { describe, expect, it } from 'vitest'
import { assertNoDrafts } from '../../src/lib/drafts'

const entries = [
  { id: 'lines-categorized', data: { draft: true } },
  { id: 'savings-found', data: { draft: false } },
]

describe('assertNoDrafts', () => {
  it('fails a production build and names the draft entry', () => {
    expect(() => assertNoDrafts('outcomes', entries, true)).toThrow(
      /lines-categorized/,
    )
  })

  it('allows drafts outside production', () => {
    expect(() => assertNoDrafts('outcomes', entries, false)).not.toThrow()
  })

  it('allows approved entries in production', () => {
    expect(() => assertNoDrafts('outcomes', [entries[1]], true)).not.toThrow()
  })
})
