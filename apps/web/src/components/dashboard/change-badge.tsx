import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react'
import { cn } from '#/components/ui'
import { changeOf, describeChange } from './change'
import type { Money } from '#/lib/api/types'

/** The change from the comparison period, as a small marked figure; nothing when neither had spend. */
export function ChangeBadge({
  now,
  before,
  className,
}: {
  now: Money
  before: Money
  className?: string
}) {
  const change = changeOf(now, before)
  if (change.kind === 'none') {
    return null
  }
  const Icon =
    change.kind === 'up'
      ? ArrowUpRight
      : change.kind === 'down'
        ? ArrowDownRight
        : Minus
  return (
    <span
      className={cn(
        'inline-flex items-center gap-0.5 text-xs font-medium tabular-nums',
        change.kind === 'up' && 'text-warning',
        change.kind === 'down' && 'text-success',
        (change.kind === 'flat' || change.kind === 'new') &&
          'text-muted-foreground',
        className,
      )}
    >
      {change.kind === 'new' ? null : (
        <Icon aria-hidden="true" className="size-3.5" />
      )}
      {describeChange(change)}
    </span>
  )
}
