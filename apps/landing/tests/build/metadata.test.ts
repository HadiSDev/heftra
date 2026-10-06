import { describe, expect, it } from 'vitest'
import { distTextFiles, readDist } from './dist'
import { readFileSync } from 'node:fs'

function meta(
  html: string,
  attribute: 'name' | 'property',
  key: string,
): string | undefined {
  const pattern = new RegExp(`<meta ${attribute}="${key}" content="([^"]*)"`)
  return html.match(pattern)?.[1]
}

const pages = [
  'index.html',
  'demo/index.html',
  'privacy/index.html',
  'terms/index.html',
]

describe('search and sharing metadata', () => {
  const home = readDist('index.html')

  it('shares as Heftra with the tagline and an absolute OG image', () => {
    expect(meta(home, 'property', 'og:title')).toBe('Heftra')
    expect(meta(home, 'property', 'og:description')).toContain(
      'Know the true price of everything you buy.',
    )
    expect(meta(home, 'property', 'og:image')).toMatch(
      /^https?:\/\/.+\/og-image-1200x630\.png$/,
    )
  })

  it('links the favicon set and the brand theme colour', () => {
    expect(home).toContain('href="/favicon.ico"')
    expect(home).toContain('href="/favicon.svg"')
    expect(home).toContain('href="/apple-touch-icon.png"')
    expect(meta(home, 'name', 'theme-color')).toBe('#0A0A0A')
  })

  it('gives every page a unique title, a description and a canonical URL', () => {
    const titles = pages.map(
      (page) => readDist(page).match(/<title>([^<]+)<\/title>/)?.[1],
    )
    expect(new Set(titles).size).toBe(pages.length)
    pages.forEach((page) => {
      const html = readDist(page)
      expect(meta(html, 'name', 'description')).toBeTruthy()
      expect(html).toMatch(/<link rel="canonical" href="https?:\/\/[^"]+"/)
      expect(html).toContain('<html lang="en"')
    })
  })

  it('embeds Organization and SoftwareApplication data on the home page', () => {
    expect(home).toContain('"@type":"Organization"')
    expect(home).toContain('"@type":"SoftwareApplication"')
  })

  it('lists every page in the sitemap and none of the error pages', () => {
    const sitemap = readDist('sitemap-0.xml')
    ;['/', '/demo', '/privacy', '/terms'].forEach((path) => {
      expect(sitemap).toMatch(
        new RegExp(
          `<loc>https?://[^<]+${path === '/' ? '/' : `${path}/?`}</loc>`,
        ),
      )
    })
    expect(sitemap).not.toContain('404')
  })

  it('points robots.txt at the sitemap', () => {
    expect(readDist('robots.txt')).toMatch(
      /^Sitemap: https?:\/\/.+\/sitemap-index\.xml$/m,
    )
  })
})

describe('product name', () => {
  it('never shows a legacy product name', () => {
    for (const file of distTextFiles()) {
      const content = readFileSync(file, 'utf8').toLowerCase()
      expect(content.includes('spend predictor'), file).toBe(false)
      expect(content.includes('erpsaa'), file).toBe(false)
      expect(content.includes('steelyard'), file).toBe(false)
    }
  })

  it('publishes contact addresses only on heftra.com', () => {
    const addresses = distTextFiles().flatMap((file) =>
      Array.from(
        readFileSync(file, 'utf8').matchAll(/[\w.+-]+@heftra\.[a-z]+/gi),
        (match) => match[0].toLowerCase(),
      ),
    )
    expect(addresses.length).toBeGreaterThan(0)
    expect(
      addresses.filter((address) => !address.endsWith('@heftra.com')),
    ).toEqual([])
  })
})
