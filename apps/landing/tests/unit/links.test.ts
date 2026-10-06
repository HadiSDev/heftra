import { describe, expect, it } from 'vitest'
import { buildLinks } from '../../src/lib/links'

describe('buildLinks', () => {
  const links = buildLinks(
    'https://app.heftra.com',
    'https://api.heftra.com',
  )

  it('points sign-in at the web app', () => {
    expect(links.signIn).toBe('https://app.heftra.com/sign-in')
  })

  it('sends every demo CTA to the on-site request form', () => {
    expect(links.demo).toBe('/demo/')
  })

  it('posts demo requests to the public web API route', () => {
    expect(links.demoRequestEndpoint).toBe(
      'https://api.heftra.com/api/v1/public/demo-requests',
    )
  })

  it('drops trailing slashes from configured origins', () => {
    const local = buildLinks('http://localhost:3100/', 'http://localhost:8100/')
    expect(local.signIn).toBe('http://localhost:3100/sign-in')
    expect(local.demoRequestEndpoint).toBe(
      'http://localhost:8100/api/v1/public/demo-requests',
    )
  })

  it('never links to a sign-up route', () => {
    expect(Object.values(links).some((href) => href.includes('/sign-up'))).toBe(
      false,
    )
  })
})
