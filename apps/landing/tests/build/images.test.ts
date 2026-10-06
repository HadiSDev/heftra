import { describe, expect, it } from 'vitest'
import { readDist } from './dist'

const pages = [
  'index.html',
  'demo/index.html',
  'privacy/index.html',
  'terms/index.html',
  '404.html',
]

function imageSources(html: string): Array<string> {
  const sources = Array.from(
    html.matchAll(/<(?:img|source)\b[^>]*?\s(?:src|srcset)="([^"]+)"/g),
    (match) => match[1],
  )
  return sources.flatMap((value) =>
    value.split(',').map((candidate) => candidate.trim().split(/\s+/)[0]),
  )
}

describe('images go through astro:assets', () => {
  it.each(pages)('%s serves every image from /_astro/', (page) => {
    imageSources(readDist(page)).forEach((source) => {
      expect(source, source).toMatch(/^\/_astro\//)
    })
  })

  it('serves product screenshots as AVIF and WebP', () => {
    const home = readDist('index.html')
    expect(home).toMatch(/<source[^>]+type="image\/avif"/)
    expect(home).toMatch(/<source[^>]+type="image\/webp"/)
  })

  it('keeps ERP logos as SVG and masks single-colour logos with an asset URL', () => {
    const home = readDist('index.html')
    expect(home).toMatch(
      /<img[^>]+src="\/_astro\/[^"]+\.svg"[^>]+alt="SAP"|<img[^>]+alt="SAP"[^>]+src="\/_astro\/[^"]+\.svg"/,
    )
    const masks = Array.from(
      home.matchAll(
        /--logo: url\(&quot;([^&]+)&quot;\)|--logo: url\("([^"]+)"\)/g,
      ),
      (match) => match[1] ?? match[2],
    )
    expect(masks.length).toBeGreaterThan(0)
    masks.forEach((url) => {
      expect(url).toMatch(/^\/_astro\/[^"]+\.svg$/)
    })
  })
})
