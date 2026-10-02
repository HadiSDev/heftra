import type { Attribute, Specification } from '#/lib/api/alternative-types'

/** A new, empty key attribute. */
export function emptyAttribute(): Attribute {
  return {
    name: '',
    kind: 'other',
    value: '',
    number: null,
    unit: null,
    direction: 'more',
    family: null,
    tier: null,
    generation: null,
  }
}

/** A number typed in a field, with a comma read as the decimal point; null when blank. */
export function parseNumber(text: string): number | null {
  const trimmed = text.trim().replace(',', '.')
  if (trimmed === '') {
    return null
  }
  const parsed = Number(trimmed)
  return Number.isFinite(parsed) ? parsed : null
}

/** Blank text as null, the rest trimmed. */
export function optionalText(text: string): string | null {
  const trimmed = text.trim()
  return trimmed === '' ? null : trimmed
}

/** Why the specification can't be saved, or null when it can. */
export function specProblem(spec: Specification): string | null {
  if (!spec.product_type.trim() || !spec.name.trim()) {
    return 'Say what the product is and what it is called.'
  }
  if (spec.units_per_line_unit !== null && spec.units_per_line_unit <= 0) {
    return 'Units per line must be more than nothing.'
  }
  const unnamed = spec.attributes.some((attribute) => !attribute.name.trim())
  if (unnamed) {
    return 'Every attribute needs a name.'
  }
  const numberless = spec.attributes.some(
    (attribute) => attribute.kind === 'numeric' && attribute.number === null,
  )
  if (numberless) {
    return 'A number attribute needs its number.'
  }
  return null
}

/** The specification as it is sent: names in snake_case, values filled in for numbers. */
export function specToSend(spec: Specification): Specification {
  return {
    ...spec,
    product_type: spec.product_type.trim(),
    name: spec.name.trim(),
    attributes: spec.attributes.map((attribute) => ({
      ...attribute,
      name: attribute.name
        .trim()
        .toLowerCase()
        .replace(/[\s-]+/g, '_'),
      value:
        attribute.kind === 'numeric' && attribute.number !== null
          ? `${attribute.number} ${attribute.unit ?? ''}`.trim()
          : attribute.value.trim(),
    })),
  }
}
