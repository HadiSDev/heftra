import { describe, expect, it } from 'vitest'
import {
  breadcrumbJsonLd,
  faqPageJsonLd,
  organizationJsonLd,
  serializeJsonLd,
  softwareApplicationJsonLd,
  websiteJsonLd,
} from '../../src/lib/seo'

const siteUrl = 'https://steelyard.com/'

describe('organizationJsonLd', () => {
  it('describes the organization with a sales contact', () => {
    const data = organizationJsonLd({
      name: 'Steelyard',
      siteUrl,
      logoUrl: 'https://steelyard.com/favicon-512.png',
      email: 'hello@steelyard.com',
    })
    expect(data['@type']).toBe('Organization')
    expect(data['@id']).toBe('https://steelyard.com/#organization')
    expect(data.contactPoint).toMatchObject({
      contactType: 'sales',
      email: 'hello@steelyard.com',
    })
  })
})

describe('websiteJsonLd', () => {
  it('names the site and links its publisher', () => {
    const data = websiteJsonLd('Steelyard', siteUrl)
    expect(data).toMatchObject({
      '@type': 'WebSite',
      url: siteUrl,
      publisher: { '@id': 'https://steelyard.com/#organization' },
    })
  })
})

describe('softwareApplicationJsonLd', () => {
  const data = softwareApplicationJsonLd({
    name: 'Steelyard',
    description: 'Spend analytics',
    siteUrl,
    imageUrl: 'https://steelyard.com/og-image-1200x630.png',
    plans: [
      { name: 'Starter', monthlyPriceEur: 249 },
      { name: 'Growth', monthlyPriceEur: 690 },
    ],
  })

  it('lists one monthly EUR offer per priced plan', () => {
    expect(data.offers).toHaveLength(2)
    expect(data.offers[1]).toMatchObject({
      name: 'Growth',
      price: '690.00',
      priceCurrency: 'EUR',
      priceSpecification: { unitText: 'MONTH', valueAddedTaxIncluded: false },
    })
  })

  it('is a business application', () => {
    expect(data.applicationCategory).toBe('BusinessApplication')
  })
})

describe('breadcrumbJsonLd', () => {
  it('numbers the trail from one', () => {
    const data = breadcrumbJsonLd([
      { name: 'Home', url: siteUrl },
      { name: 'Privacy policy', url: 'https://steelyard.com/privacy/' },
    ])
    expect(data.itemListElement.map((item) => item.position)).toEqual([1, 2])
    expect(data.itemListElement[1].item).toBe('https://steelyard.com/privacy/')
  })
})

describe('faqPageJsonLd', () => {
  it('has one question per FAQ item, in order', () => {
    const items = [
      { question: 'Which ERPs?', answer: 'Billy today.' },
      { question: 'Where is data hosted?', answer: 'In the EU.' },
    ]
    const data = faqPageJsonLd(items)
    expect(data.mainEntity.map((entity) => entity.name)).toEqual([
      'Which ERPs?',
      'Where is data hosted?',
    ])
    expect(data.mainEntity[1].acceptedAnswer.text).toBe('In the EU.')
  })
})

describe('serializeJsonLd', () => {
  it('escapes angle brackets so content cannot close the script tag', () => {
    expect(serializeJsonLd({ text: '</script>' })).not.toContain('</script>')
  })
})
