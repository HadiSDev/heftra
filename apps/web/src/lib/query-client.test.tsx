import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { ToastProvider, toastManager } from '#/components/ui'
import { ApiError } from '#/lib/api/api-client'
import { DEMO_REFUSAL } from '#/lib/api/demo-refusal'
import { DEMO_NOTICE } from '#/lib/demo/demo-notice'
import { createQueryClient } from './query-client'

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

async function failMutation(error: unknown) {
  const client = createQueryClient()
  render(<ToastProvider>{null}</ToastProvider>)
  const mutation = client.getMutationCache().build(client, {
    mutationFn: () => Promise.reject(error),
  })
  await mutation.execute(undefined).catch(() => undefined)
}

describe('createQueryClient', () => {
  it('announces a change the demo refused', async () => {
    await failMutation(new ApiError(403, 'Forbidden', { detail: DEMO_REFUSAL }))

    expect(await screen.findByText(DEMO_NOTICE.title)).toBeTruthy()
  })

  it('leaves any other failure to the form that made it', async () => {
    const add = vi.spyOn(toastManager, 'add')

    await failMutation(
      new ApiError(403, 'Forbidden', { detail: 'Requires an admin.' }),
    )

    expect(add).not.toHaveBeenCalled()
  })
})
