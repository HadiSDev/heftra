import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

const webStyles = readFileSync(
  new URL('../../../web/src/styles.css', import.meta.url),
  'utf8',
)
const landingTokens = readFileSync(
  new URL('../../src/styles/tokens.css', import.meta.url),
  'utf8',
)
const landingTheme = readFileSync(
  new URL('../../src/styles/theme.css', import.meta.url),
  'utf8',
)

function block(css: string, selector: RegExp): string {
  const match = css.match(selector)
  if (!match) {
    throw new Error(`No block matches ${selector}`)
  }
  return match[1]
}

function declarations(body: string): Map<string, string> {
  const result = new Map<string, string>()
  const pattern = /(--[\w-]+)\s*:\s*([^;]+);/g
  for (const [, name, value] of body.matchAll(pattern)) {
    result.set(name, value.replace(/\s+/g, ' ').trim())
  }
  return result
}

const scopes: Array<[string, RegExp]> = [
  ['light (:root)', /:root \{([\s\S]*?)\n\}/],
  ['dark (.dark)', /\n\.dark \{([\s\S]*?)\n\}/],
  ['theme (@theme inline)', /@theme inline \{([\s\S]*?)\n\}/],
]

describe('design tokens mirror the web app', () => {
  it.each(scopes)('%s tokens match apps/web', (_, selector) => {
    const web = declarations(block(webStyles, selector))
    const landingSource = selector.source.startsWith('@theme')
      ? landingTheme
      : landingTokens
    const landing = declarations(block(landingSource, selector))
    expect(web.size).toBeGreaterThan(0)
    for (const [name, value] of web) {
      expect(landing.get(name), name).toBe(value)
    }
  })
})
