import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { anchorsWithText, distTextFiles, hrefsOf, readDist } from './dist'

const home = readDist('index.html')
const env = readFileSync(new URL('../../.env', import.meta.url), 'utf8')

function envValue(name: string): string {
  const match = env.match(new RegExp(`^${name}=(.*)$`, 'm'))
  if (!match) {
    throw new Error(`${name} is not set in .env`)
  }
  return match[1].trim()
}

describe('home page structure', () => {
  it('has exactly one h1', () => {
    expect(home.match(/<h1\b/g)).toHaveLength(1)
  })

  it.each(['product', 'how-it-works', 'security', 'pricing', 'faq'])(
    'has the #%s anchor',
    (id) => {
      expect(home).toContain(`id="${id}"`)
    },
  )

  it('has a header with navigation, a main landmark and a footer', () => {
    expect(home).toMatch(/<header\b[\s\S]*<nav\b[\s\S]*<\/header>/)
    expect(home).toContain('<main id="main"')
    expect(home).toMatch(/<footer\b/)
  })

  it('renders no testimonials section while there are no testimonials', () => {
    expect(home).not.toContain('testimonials-title')
  })

  it('renders every FAQ entry and the same questions in FAQPage data', () => {
    const details = home.match(/<details\b/g) ?? []
    const jsonLd =
      home.match(
        /<script type="application\/ld\+json">([\s\S]*?)<\/script>/g,
      ) ?? []
    const faq = jsonLd
      .map((block) => JSON.parse(block.replace(/<[^>]+>/g, '')))
      .find((data) => data['@type'] === 'FAQPage')
    expect(faq.mainEntity).toHaveLength(details.length)
  })
})

describe('calls to action', () => {
  const pages = [
    'index.html',
    'demo/index.html',
    'privacy/index.html',
    'terms/index.html',
    '404.html',
  ]

  it.each(pages)('%s sends Sign in to the web app', (page) => {
    const signIn = anchorsWithText(readDist(page), 'Sign in')
    expect(signIn.length).toBeGreaterThan(0)
    signIn.forEach((href) => {
      expect(href).toBe(
        `${envValue('PUBLIC_APP_URL').replace(/\/$/, '')}/sign-in`,
      )
    })
  })

  it.each(pages)('%s sends Get a demo to /demo', (page) => {
    const demo = anchorsWithText(readDist(page), 'Get a demo')
    expect(demo.length).toBeGreaterThan(0)
    demo.forEach((href) => {
      expect(href).toBe('/demo/')
    })
  })

  it.each(pages)('%s never links to sign-up', (page) => {
    expect(
      hrefsOf(readDist(page)).some((href) => href.includes('/sign-up')),
    ).toBe(false)
  })
})

describe('the booking link is gated', () => {
  it('appears nowhere in the built site', () => {
    const forbidden = [
      process.env.DEMO_BOOKING_URL,
      'cal.com',
      'calendly.com',
    ].filter((value): value is string => Boolean(value))
    for (const file of distTextFiles()) {
      const content = readFileSync(file, 'utf8')
      for (const value of forbidden) {
        expect(content.includes(value), `${value} found in ${file}`).toBe(false)
      }
    }
  })
})

describe('product imagery', () => {
  it('has no screenshot placeholders left', () => {
    const pending = Array.from(
      home.matchAll(/data-screenshot-pending="([^"]+)"/g),
      (match) => match[1],
    )
    expect(
      pending,
      `capture these screenshots: ${[...new Set(pending)].join(', ')}`,
    ).toEqual([])
  })
})
