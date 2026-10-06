import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import {
  LOCKUP_MARK_TRANSFORM,
  MARK,
  SMALL_MARK,
  WORDMARK_PATH,
} from '../../src/components/brand/geometry'
import type { MarkShape } from '../../src/components/brand/geometry'

const brandRoot = new URL('../../../../brand/', import.meta.url)

function readBrand(path: string): string {
  return readFileSync(new URL(path, brandRoot), 'utf8')
}

function shapeMarkup(shapes: Array<MarkShape>): string {
  return shapes
    .map((shape) => {
      if (shape.kind === 'circle') {
        return `<circle cx="${shape.cx}" cy="${shape.cy}" r="${shape.r}"/>`
      }
      return `<rect x="${shape.x}" y="${shape.y}" width="${shape.width}" height="${shape.height}"/>`
    })
    .join('')
}

describe('logo geometry', () => {
  it('uses the wordmark outline from the lockup SVG verbatim', () => {
    expect(readBrand('svg/steelyard-lockup-black.svg')).toContain(
      `d="${WORDMARK_PATH}"`,
    )
  })

  it('uses the mark from the symbol SVG', () => {
    expect(readBrand('svg/steelyard-symbol-black.svg')).toContain(
      shapeMarkup(MARK),
    )
  })

  it('uses the thicker-armed mark from the favicon', () => {
    expect(readBrand('favicon/favicon.svg')).toContain(shapeMarkup(SMALL_MARK))
  })

  it('places the mark in the lockup as the pack does', () => {
    const lockup = readBrand('svg/steelyard-lockup-black.svg')
    expect(lockup).toContain(shapeMarkup(MARK))
    expect(lockup).toMatch(
      /translate\(-15\.975(0+1)? -53\.25\) scale\(2\.6625\)/,
    )
    expect(LOCKUP_MARK_TRANSFORM).toBe(
      'translate(-15.975 -53.25) scale(2.6625)',
    )
  })
})
