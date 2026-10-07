/** Typed access to the Vite-exposed environment. */

/** Base URL of the web API (no trailing slash). */
export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(
    /\/$/,
    '',
  ) ?? 'http://localhost:8100'

/** Clerk publishable key. */
export const CLERK_PUBLISHABLE_KEY = import.meta.env
  .VITE_CLERK_PUBLISHABLE_KEY as string | undefined

/** Whether to offer Google OAuth on the sign-in page. */
export const GOOGLE_OAUTH_ENABLED =
  (import.meta.env.VITE_CLERK_GOOGLE_OAUTH as string | undefined) === 'true'

/** Throws a readable error when required config is missing. */
export function assertRequiredEnv(): void {
  if (!CLERK_PUBLISHABLE_KEY) {
    throw new Error(
      'Missing VITE_CLERK_PUBLISHABLE_KEY. Copy apps/web/.env.example to .env and set it ' +
        'to your Clerk publishable key.',
    )
  }
}

/** A shared login shown on the sign-in page. Set only for the hosted demo. */
export interface DemoLogin {
  email: string
  password: string
}

function readDemoLogin(): DemoLogin | null {
  const email = import.meta.env.VITE_DEMO_EMAIL as string | undefined
  const password = import.meta.env.VITE_DEMO_PASSWORD as string | undefined
  if (!email || !password) {
    return null
  }
  return { email, password }
}

export const DEMO_LOGIN: DemoLogin | null = readDemoLogin()
