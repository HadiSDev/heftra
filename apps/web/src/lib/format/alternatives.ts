import type {
  AlternativeMatch,
  AlternativeRead,
  AlternativeReviewStatus,
  AlternativeSource,
  DismissReason,
  ItemClass,
  PriceNote,
  PricingUnit,
  Verdict,
} from '#/lib/api/alternative-types'
import type { BadgeVariant } from './agreements'
import { formatDay, formatMoney } from './format'

export const SOURCE_LABELS: Record<AlternativeSource, string> = {
  history: 'Your purchases',
  benchmark: 'Other customers',
  marketplace: 'Marketplaces',
}

export const MATCH_LABELS: Record<AlternativeMatch, string> = {
  exact: 'Exact',
  equivalent: 'Equivalent',
}

export const MATCH_VARIANTS: Record<AlternativeMatch, BadgeVariant> = {
  exact: 'success',
  equivalent: 'info',
}

export const CLASS_LABELS: Record<ItemClass, string> = {
  material: 'Material',
  part: 'Part',
  finished_good: 'Finished good',
  service: 'Service',
}

export const VERDICT_LABELS: Record<Verdict, string> = {
  same: 'Same',
  better: 'Better',
  worse: 'Worse',
  missing: 'Not stated',
}

export const VERDICT_VARIANTS: Record<Verdict, BadgeVariant> = {
  same: 'outline',
  better: 'success',
  worse: 'destructive',
  missing: 'warning',
}

export const REVIEW_LABELS: Record<AlternativeReviewStatus, string> = {
  open: 'Open',
  dismissed: 'Dismissed',
  switched: 'Switched',
}

export const DISMISS_REASON_LABELS: Record<DismissReason, string> = {
  not_equivalent: 'Not equivalent',
  supplier_not_approved: 'Supplier not approved',
  price_wrong: 'Price is wrong',
  other: 'Other',
}

const UNIT_LABELS: Record<PricingUnit, string> = {
  kg: 'kg',
  m: 'm',
  m2: 'm²',
  m3: 'm³',
  l: 'l',
  piece: 'piece',
  sheet: 'sheet',
  roll: 'roll',
  pack: 'pack',
}

export const PRICING_UNITS = Object.keys(UNIT_LABELS) as Array<PricingUnit>

export function unitLabel(unit: PricingUnit | null): string {
  return unit ? UNIT_LABELS[unit] : 'unit'
}

export const PRICE_NOTES: Record<PriceNote, string> = {
  not_bought: 'Not bought in the last 12 months.',
  no_specification: 'Its specification hasn’t been read yet.',
  no_pack_size:
    'How many units a line holds isn’t known; correct the specification.',
  no_quantity:
    'Its lines don’t state a quantity, so there is no price per unit.',
}

/** A price per pricing unit, e.g. "DKK 2.40 per m". */
export function perUnit(
  amount: AlternativeRead['unit_price'] | null,
  currency: string | null,
  unit: PricingUnit | null,
): string {
  if (amount === null) {
    return '—'
  }
  return `${formatMoney(amount, currency)} per ${unitLabel(unit)}`
}

/** Where an alternative was found, in a line. */
export function originText(alternative: AlternativeRead): string {
  const origin = alternative.origin
  if (alternative.source === 'history') {
    const when = origin.last_bought_on
      ? `, last bought ${formatDay(origin.last_bought_on)}`
      : ''
    return `Bought from ${origin.supplier ?? 'another supplier'} by ${origin.company ?? 'your organization'}${when}`
  }
  if (alternative.source === 'benchmark') {
    return `Median of ${origin.organizations ?? 0} other organizations; the cheapest quarter pay ${formatMoney(origin.lowest_quartile ?? 0, alternative.currency)} or less`
  }
  const seen = origin.seen_at ? `, seen ${formatDay(origin.seen_at)}` : ''
  return `${origin.seller ?? 'A seller'}${seen}`
}
