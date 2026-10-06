import { describe, expect, it } from 'vitest'
import { hrefsOf, readDist } from './dist'

const indexedPages = [
  'index.html',
  'demo/index.html',
  'privacy/index.html',
  'terms/index.html',
]

function jsonLdTypes(html: string): Array<string> {
  const blocks = html.match(
    /<script type="application\/ld\+json">([\s\S]*?)<\/script>/g,
  )
  return (blocks ?? []).map(
    (block) => JSON.parse(block.replace(/<[^>]+>/g, ''))['@type'],
  )
}

function jsonLd(html: string, type: string) {
  const blocks =
    html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g) ??
    []
  return blocks
    .map((block) => JSON.parse(block.replace(/<[^>]+>/g, '')))
    .find((data) => data['@type'] === type)
}

describe('snippets fit the search results', () => {
  it.each(indexedPages)('%s has a title of at most 60 characters', (page) => {
    const title = readDist(page).match(/<title>([^<]+)<\/title>/)?.[1] ?? ''
    expect(title.length).toBeGreaterThan(10)
    expect(title.length).toBeLessThanOrEqual(60)
  })

  it.each(indexedPages)(
    '%s has a description of 70 to 160 characters',
    (page) => {
      const description =
        readDist(page).match(
          /<meta name="description" content="([^"]*)"/,
        )?.[1] ?? ''
      expect(description.length).toBeGreaterThanOrEqual(70)
      expect(description.length).toBeLessThanOrEqual(160)
    },
  )
})

describe('indexing', () => {
  it.each(indexedPages)('%s is indexable', (page) => {
    expect(readDist(page)).toContain(
      '<meta name="robots" content="index, follow',
    )
  })

  it('keeps the 404 page out of the index', () => {
    const notFound = readDist('404.html')
    expect(notFound).toContain('<meta name="robots" content="noindex, follow">')
    expect(notFound).not.toContain('rel="canonical"')
  })

  it.each(indexedPages)(
    '%s links internal pages with the canonical trailing slash',
    (page) => {
      const internal = hrefsOf(readDist(page)).filter(
        (href) =>
          href.startsWith('/') &&
          !href.startsWith('//') &&
          !href.startsWith('/_astro/') &&
          !/\.[a-z0-9]+$/i.test(href.split('#')[0]),
      )
      internal.forEach((href) => {
        expect(href.split('#')[0], href).toMatch(/\/$/)
      })
    },
  )
})

describe('structured data', () => {
  const home = readDist('index.html')

  it('describes the website, organization and application on the home page', () => {
    expect(jsonLdTypes(home)).toEqual(
      expect.arrayContaining([
        'WebSite',
        'Organization',
        'SoftwareApplication',
        'FAQPage',
      ]),
    )
  })

  it('offers every priced plan', () => {
    const application = jsonLd(home, 'SoftwareApplication')
    const pricedCards =
      (home.match(/class="price-monthly[^"]*"/g) ?? []).length / 2
    expect(application.offers).toHaveLength(pricedCards)
  })

  it.each(['demo/index.html', 'privacy/index.html', 'terms/index.html'])(
    '%s has a breadcrumb back to the home page',
    (page) => {
      const breadcrumb = jsonLd(readDist(page), 'BreadcrumbList')
      expect(breadcrumb.itemListElement).toHaveLength(2)
      expect(breadcrumb.itemListElement[0].item).toMatch(/\/$/)
    },
  )
})

describe('performance hints and discovery files', () => {
  it('preloads the headline font from the same file the stylesheet uses', () => {
    const home = readDist('index.html')
    const preload = home.match(
      /<link rel="preload" href="([^"]+\.woff2)" as="font"/,
    )?.[1]
    expect(preload).toBeTruthy()
  })

  it('serves a web manifest with the brand colour and icons', () => {
    const manifest = JSON.parse(readDist('site.webmanifest'))
    expect(manifest.name).toBe('Heftra')
    expect(manifest.theme_color).toBe('#0A0A0A')
    expect(manifest.icons.map((icon: { sizes: string }) => icon.sizes)).toEqual(
      ['192x192', '512x512'],
    )
  })

  it('publishes llms.txt with the product, features, pricing and FAQ', () => {
    const llms = readDist('llms.txt')
    expect(llms.startsWith('# Heftra')).toBe(true)
    expect(llms).toContain('## Features')
    expect(llms).toContain('## Pricing')
    expect(llms).toContain('## FAQ')
  })

  it('stamps sitemap entries with a last-modified date', () => {
    expect(readDist('sitemap-0.xml')).toMatch(/<lastmod>\d{4}-\d{2}-\d{2}/)
  })
})
