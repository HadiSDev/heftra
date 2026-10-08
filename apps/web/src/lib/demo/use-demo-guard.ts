import * as React from 'react'
import { DemoRefusalError } from '#/lib/api/demo-refusal'
import { usePrincipal } from '#/lib/auth/auth'
import { announceDemoRefusal } from './demo-notice'

/**
 * Wraps a write that bypasses the web API (e.g. a Clerk call) so the demo
 * login never runs it: instead it announces the refusal and rejects with a
 * `DemoRefusalError`, which the caller's error display shows like an API refusal.
 */
export function useDemoGuard() {
  const { demo } = usePrincipal()

  return React.useCallback(
    <TArgs extends Array<unknown>, TResult>(
      action: (...args: TArgs) => Promise<TResult>,
    ) =>
      (...args: TArgs): Promise<TResult> => {
        if (demo) {
          announceDemoRefusal()
          return Promise.reject(new DemoRefusalError())
        }
        return action(...args)
      },
    [demo],
  )
}
