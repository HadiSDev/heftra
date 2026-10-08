import { ApiError } from './api-client'

/** The web API's refusal of any change made by the hosted demo's shared login. */
export const DEMO_REFUSAL = "This is a demo, so changes aren't saved."

/** Raised in the browser for a demo change that would bypass the web API (e.g. a Clerk write). */
export class DemoRefusalError extends Error {
  constructor() {
    super(DEMO_REFUSAL)
    this.name = 'DemoRefusalError'
  }
}

/** Whether `error` is the demo's refusal to save a change. */
export function isDemoRefusal(error: unknown): boolean {
  if (error instanceof DemoRefusalError) {
    return true
  }
  return (
    error instanceof ApiError &&
    error.status === 403 &&
    error.detail === DEMO_REFUSAL
  )
}
