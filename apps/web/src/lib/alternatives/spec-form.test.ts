import { describe, expect, it } from 'vitest'
import type { Specification } from '#/lib/api/alternative-types'
import {
  emptyAttribute,
  parseNumber,
  specProblem,
  specToSend,
} from './spec-form'

const SPEC: Specification = {
  item_class: 'finished_good',
  product_type: 'business laptop',
  name: 'ThinkPad T14',
  brand: 'Lenovo',
  model: null,
  part_number: null,
  gtin: null,
  attributes: [],
  pricing_unit: 'piece',
  units_per_line_unit: 1,
  confidence: 0.9,
}

describe('spec form', () => {
  it('reads numbers with a decimal comma', () => {
    expect(parseNumber('2,5')).toBe(2.5)
    expect(parseNumber(' ')).toBeNull()
    expect(parseNumber('many')).toBeNull()
  })

  it('needs names and numbers', () => {
    expect(specProblem({ ...SPEC, name: ' ' })).toBe(
      'Say what the product is and what it is called.',
    )
    expect(
      specProblem({
        ...SPEC,
        attributes: [{ ...emptyAttribute(), name: 'memory', kind: 'numeric' }],
      }),
    ).toBe('A number attribute needs its number.')
    expect(specProblem(SPEC)).toBeNull()
  })

  it('sends snake_case names and a number as its value', () => {
    const sent = specToSend({
      ...SPEC,
      attributes: [
        {
          ...emptyAttribute(),
          name: 'Screen size',
          kind: 'numeric',
          number: 14,
          unit: 'in',
        },
      ],
    })
    expect(sent.attributes[0]).toMatchObject({
      name: 'screen_size',
      value: '14 in',
    })
  })
})
