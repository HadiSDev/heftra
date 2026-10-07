/** The hosted demo's shared login, shown above the sign-in form. */
import * as React from 'react'
import { Button } from '#/components/ui'
import type { DemoLogin } from '#/lib/env'

export interface DemoAccessProps {
  login: DemoLogin
  onSignIn: () => Promise<void>
}

export function DemoAccess({ login, onSignIn }: DemoAccessProps) {
  const [pending, setPending] = React.useState(false)

  async function signIn() {
    setPending(true)
    try {
      await onSignIn()
    } finally {
      setPending(false)
    }
  }

  return (
    <section
      aria-labelledby="demo-access-title"
      className="mb-5 rounded-lg border border-border bg-muted/50 p-4"
    >
      <h2 id="demo-access-title" className="text-sm font-semibold">
        Demo access
      </h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Explore the fictional company Nordlys Byg A/S. Nothing can be changed.
      </p>
      <dl className="mt-3 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm">
        <dt className="text-muted-foreground">Email</dt>
        <dd className="font-mono break-all select-all">{login.email}</dd>
        <dt className="text-muted-foreground">Password</dt>
        <dd className="font-mono break-all select-all">{login.password}</dd>
      </dl>
      <Button
        type="button"
        className="mt-4 w-full"
        disabled={pending}
        onClick={signIn}
      >
        {pending ? 'Signing in…' : 'Sign in to the demo'}
      </Button>
    </section>
  )
}
