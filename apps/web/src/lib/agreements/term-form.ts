import type {
  AgreementTermKind,
  RebateTier,
  TermFields,
  TermRead,
} from '#/lib/api/agreement-types'

/** A term's fields as the form edits them: text, whatever the field. */
export interface TermFormValues {
  scope: string
  conditions: string
  item: string
  unit: string
  unit_price: string
  discount_percent: string
  commitment_amount: string
  commitment_period: string
  currency: string
  /** One tier per line, "threshold = rebate%". */
  tiers: string
}

export const EMPTY_TERM_VALUES: TermFormValues = {
  scope: '',
  conditions: '',
  item: '',
  unit: '',
  unit_price: '',
  discount_percent: '',
  commitment_amount: '',
  commitment_period: 'year',
  currency: '',
  tiers: '',
}

function text(value: string | number | null): string {
  return value === null ? '' : String(value)
}

export function termValues(term: TermRead): TermFormValues {
  return {
    scope: term.scope,
    conditions: text(term.conditions),
    item: text(term.item),
    unit: text(term.unit),
    unit_price: text(term.unit_price),
    discount_percent: text(term.discount_percent),
    commitment_amount: text(term.commitment_amount),
    commitment_period: term.commitment_period ?? 'year',
    currency: text(term.currency),
    tiers: (term.tiers ?? [])
      .map((tier) => `${tier.threshold} = ${tier.rebate_percent}%`)
      .join('\n'),
  }
}

function optional(value: string): string | null {
  const trimmed = value.trim()
  return trimmed === '' ? null : trimmed
}

function amount(value: string): string | null {
  const trimmed = value.trim().replace(/\s/g, '').replace(',', '.')
  return trimmed === '' ? null : trimmed
}

/** Tiers from "threshold = rebate%" lines; lines that aren't one are left out. */
export function parseTiers(value: string): Array<RebateTier> {
  return value
    .split('\n')
    .map((line) => /^\s*([\d.,\s]+?)\s*=\s*([\d.,]+)\s*%?\s*$/.exec(line))
    .filter((match): match is RegExpExecArray => match !== null)
    .map((match) => ({
      threshold: match[1].replace(/[\s,]/g, ''),
      rebate_percent: match[2].replace(',', '.'),
    }))
}

/** The fields to send for a term of `kind`; fields other kinds use are cleared. */
export function termFields(
  kind: AgreementTermKind,
  values: TermFormValues,
): Omit<TermFields, 'scope_category_ids'> {
  const fields: Omit<TermFields, 'scope_category_ids'> = {
    scope: values.scope.trim(),
    conditions: null,
    item: null,
    unit: null,
    unit_price: null,
    discount_percent: null,
    commitment_amount: null,
    commitment_period: null,
    tiers: null,
    currency: optional(values.currency)?.toUpperCase() ?? null,
  }
  if (kind === 'preferred_supplier') {
    fields.conditions = optional(values.conditions)
  }
  if (kind === 'agreed_price') {
    fields.item = optional(values.item)
    fields.unit = optional(values.unit)
    fields.unit_price = amount(values.unit_price)
  }
  if (kind === 'discount') {
    fields.discount_percent = amount(values.discount_percent)
  }
  if (kind === 'volume_commitment') {
    fields.commitment_amount = amount(values.commitment_amount)
    fields.commitment_period = optional(values.commitment_period)
    const tiers = parseTiers(values.tiers)
    fields.tiers = tiers.length > 0 ? tiers : null
  }
  return fields
}

/** Why the values can't be saved for `kind`, or null when they can. */
export function termProblem(
  kind: AgreementTermKind,
  values: TermFormValues,
): string | null {
  if (!values.scope.trim()) {
    return 'Say what the term covers.'
  }
  if (
    kind === 'agreed_price' &&
    (!values.item.trim() || !amount(values.unit_price))
  ) {
    return 'An agreed price needs the item and its price.'
  }
  if (kind === 'discount' && !amount(values.discount_percent)) {
    return 'A discount needs its percentage.'
  }
  if (kind === 'volume_commitment' && !amount(values.commitment_amount)) {
    return 'A commitment needs its amount.'
  }
  return null
}
