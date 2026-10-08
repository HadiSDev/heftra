import { usePrincipal } from '#/lib/auth/auth'

/** A slim strip telling demo visitors their changes aren't kept; renders nothing for anyone else. */
export function DemoBanner() {
  const { demo } = usePrincipal()

  if (!demo) {
    return null
  }

  return (
    <p
      role="status"
      className="flex shrink-0 flex-wrap items-center justify-center gap-x-2 gap-y-0.5 bg-primary px-4 py-1.5 text-center text-xs text-primary-foreground sm:text-sm"
    >
      <span className="rounded-sm border border-primary-foreground/40 px-1.5 text-[11px] font-semibold tracking-wide uppercase">
        Demo
      </span>
      <span>
        You’re exploring the Heftra demo. Try anything — changes aren’t saved,
        and the demo resets every night.
      </span>
    </p>
  )
}
