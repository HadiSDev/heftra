import type { Page } from '@playwright/test'

export type SignIn =
  | { kind: 'ticket'; url: string }
  | { kind: 'password'; email: string; password: string }

export function signInFromEnv(env: NodeJS.ProcessEnv): SignIn {
  if (env.CAPTURE_SIGN_IN_URL) {
    return { kind: 'ticket', url: env.CAPTURE_SIGN_IN_URL }
  }
  if (env.CAPTURE_LOGIN_EMAIL && env.CAPTURE_LOGIN_PASSWORD) {
    return {
      kind: 'password',
      email: env.CAPTURE_LOGIN_EMAIL,
      password: env.CAPTURE_LOGIN_PASSWORD,
    }
  }
  throw new Error(
    'Set CAPTURE_SIGN_IN_URL (from `clerk impersonate <user> --print`, dev instance) or CAPTURE_LOGIN_EMAIL and CAPTURE_LOGIN_PASSWORD.',
  )
}

export async function signIn(
  page: Page,
  method: SignIn,
  appUrl: string,
): Promise<void> {
  if (method.kind === 'ticket') {
    const ticketUrl = new URL(method.url)
    ticketUrl.searchParams.set('redirect_url', new URL('/', appUrl).href)
    await page.goto(ticketUrl.href)
  } else {
    await page.goto(new URL('/sign-in', appUrl).href, {
      waitUntil: 'networkidle',
    })
    await page.locator('input[type="email"]').first().fill(method.email)
    await page.locator('input[type="password"]').fill(method.password)
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  }
  await page.waitForURL(
    (url) =>
      url.href.startsWith(appUrl) && !url.pathname.startsWith('/sign-in'),
    { timeout: 30_000 },
  )
}
