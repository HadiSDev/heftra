import type * as React from 'react'

/** One figure of a summary card: a caption, the value, and a line saying what it means. */
export function Metric({
  caption,
  value,
  children,
}: {
  caption: string
  value: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <section
      aria-label={caption}
      className="flex min-w-0 flex-col gap-1 px-5 py-4"
    >
      <h3 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
        {caption}
      </h3>
      <div className="font-display text-2xl font-semibold tracking-tight tabular-nums">
        {value}
      </div>
      <div className="text-sm text-muted-foreground">{children}</div>
    </section>
  )
}
