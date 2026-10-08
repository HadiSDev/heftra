import * as React from 'react'
import { cn } from '../cn'

export interface AppShellProps {
  /** The sidebar element (use the `Sidebar` component). */
  sidebar: React.ReactNode
  /** Optional top bar (use the `Topbar` component). */
  header?: React.ReactNode
  /** Optional full-width strip above everything else, e.g. a notice about the session. */
  banner?: React.ReactNode
  children: React.ReactNode
  className?: string
}

/** The id of the element the page content scrolls in; the router restores and resets it. */
export const APP_SCROLL_ID = 'app-main'

/** The dashboard layout: a sidebar and top bar that stay put, and content that scrolls. */
export function AppShell({
  sidebar,
  header,
  banner,
  children,
  className,
}: AppShellProps) {
  return (
    <div
      className={cn(
        'flex h-dvh flex-col overflow-hidden bg-background',
        className,
      )}
    >
      {banner}
      <div className="mx-auto flex min-h-0 w-full max-w-[1600px] flex-1 gap-4 p-3 sm:p-4">
        {sidebar}
        <div className="flex min-h-0 min-w-0 flex-1 flex-col">
          {header}
          <main
            id={APP_SCROLL_ID}
            data-scroll-restoration-id={APP_SCROLL_ID}
            className="min-h-0 min-w-0 flex-1 overflow-y-auto [scrollbar-gutter:stable] px-2 pt-2 pb-6 sm:px-4"
          >
            {children}
          </main>
        </div>
      </div>
    </div>
  )
}
