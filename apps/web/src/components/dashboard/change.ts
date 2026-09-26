import { toNumber } from '#/lib/format/format'
import type { Money } from '#/lib/api/types'

/** How a figure moved from the comparison period. */
export type Change =
  | { kind: 'up' | 'down' | 'flat'; ratio: number }
  | { kind: 'new' }
  | { kind: 'none' }

/** The change from `before` to `now`: a ratio, "new" when there was nothing before, or none at all. */
export function changeOf(now: Money, before: Money): Change {
  const current = toNumber(now)
  const previous = toNumber(before)
  if (previous === 0) {
    return current === 0 ? { kind: 'none' } : { kind: 'new' }
  }
  const ratio = (current - previous) / Math.abs(previous)
  if (Math.abs(ratio) < 0.005) {
    return { kind: 'flat', ratio: 0 }
  }
  return { kind: ratio > 0 ? 'up' : 'down', ratio }
}

const percent = new Intl.NumberFormat('en-GB', {
  style: 'percent',
  maximumFractionDigits: 0,
})

/** A change as words: "+20%", "−12%", "0%", "New", or empty. */
export function describeChange(change: Change): string {
  switch (change.kind) {
    case 'new':
      return 'New'
    case 'none':
      return ''
    case 'flat':
      return '0%'
    case 'up':
      return `+${percent.format(change.ratio)}`
    case 'down':
      return `−${percent.format(Math.abs(change.ratio))}`
  }
}

/** A share of a whole as a percentage, "<1%" for a sliver. */
export function formatShare(share: number): string {
  if (share > 0 && share < 0.01) {
    return '<1%'
  }
  return percent.format(share)
}
