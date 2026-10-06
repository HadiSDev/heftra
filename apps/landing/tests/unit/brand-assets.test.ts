import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

const brandRoot = new URL('../../../../brand/', import.meta.url)
const publicRoot = new URL('../../public/', import.meta.url)

const servedAssets: Array<[string, string]> = [
  ['favicon.ico', 'favicon/favicon.ico'],
  ['favicon.svg', 'favicon/favicon.svg'],
  ['apple-touch-icon.png', 'favicon/apple-touch-icon.png'],
  ['favicon-192.png', 'favicon/favicon-192.png'],
  ['favicon-512.png', 'favicon/favicon-512.png'],
  ['og-image-1200x630.png', 'social/og-image-1200x630.png'],
]

describe('served brand assets', () => {
  it.each(servedAssets)('%s is a byte copy of brand/%s', (served, source) => {
    const servedBytes = readFileSync(new URL(served, publicRoot))
    const sourceBytes = readFileSync(new URL(source, brandRoot))
    expect(servedBytes.equals(sourceBytes)).toBe(true)
  })
})
