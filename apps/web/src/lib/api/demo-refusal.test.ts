import { describe, expect, it } from 'vitest'
import { ApiError } from './api-client'
import { DEMO_REFUSAL, DemoRefusalError, isDemoRefusal } from './demo-refusal'

describe('isDemoRefusal', () => {
  it('recognises the web API refusing a demo change', () => {
    expect(
      isDemoRefusal(new ApiError(403, 'Forbidden', { detail: DEMO_REFUSAL })),
    ).toBe(true)
  })

  it('recognises a demo change stopped in the browser', () => {
    expect(isDemoRefusal(new DemoRefusalError())).toBe(true)
  })

  it('ignores any other 403', () => {
    expect(
      isDemoRefusal(
        new ApiError(403, 'Forbidden', { detail: 'Requires an admin.' }),
      ),
    ).toBe(false)
  })

  it('ignores the demo message on another status', () => {
    expect(
      isDemoRefusal(new ApiError(400, 'Bad', { detail: DEMO_REFUSAL })),
    ).toBe(false)
  })

  it('ignores plain errors and non-errors', () => {
    expect(isDemoRefusal(new Error(DEMO_REFUSAL))).toBe(false)
    expect(isDemoRefusal(undefined)).toBe(false)
  })
})
