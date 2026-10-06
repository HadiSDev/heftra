import { describe, expect, it } from 'vitest'
import {
  breadcrumbJsonLd,
  faqPageJsonLd,
  organizationJsonLd,
  serializeJsonLd,
  softwareApplicationJsonLd,
  websiteJsonLd,
} from '../../src/lib/seo'

const siteUrl = 'https://heftra.com/'

describe('organizationJsonLd', () => {
  it('describes the organization with a sales contact', () => {
    const data = organizationJsonLd({
      name: 'Heftra',
      siteUrl,
      logoUrl: 'https://heftra.com/favicon-512.png',
      email: 'hello@heftra.com',
      parent: {
        legalName: 'VectorLab ApS',
        vatId: 'DK46341732',
        streetAddress: 'Gormsvej 2',
        postalCode: '4000',
        city: 'Roskilde',
        countryCode: 'DK',
        email: 'info@vectorlab.dk',
        phone: '+45 60 14 70 23',
        website: 'https://vectorlab.dk',
        sameAs: ['https://www.linkedin.com/company/vectorlab-dk'],
      },
    })
    expect(data.parentOrganization).toMatchObject({
      legalName: 'VectorLab ApS',
      vatID: 'DK46341732',
      address: { addressLocality: 'Roskilde', addressCountry: 'DK' },
    })
    expect(data['@type']).toBe('Organization')
    expect(data['@id']).toBe('https://heftra.com/#organization')
    expect(data.contactPoint).toMatchObject({
      contactType: 'sales',
      email: 'hello@heftra.com',
    })
  })
})

describe('websiteJsonLd', () => {
  it('names the site and links its publisher', () => {
    const data = websiteJsonLd('Heftra', siteUrl)
    expect(data).toMatchObject({
      '@type': 'WebSite',
      url: siteUrl,
      publisher: { '@id': 'https://heftra.com/#organization' },
    })
  })
})

describe('softwareApplicationJsonLd', () => {
  const data = softwareApplicationJsonLd({
    name: 'Heftra',
    description: 'Spend analytics',
    siteUrl,
    imageUrl: 'https://heftra.com/og-image-1200x630.png',
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
      { name: 'Privacy policy', url: 'https://heftra.com/privacy/' },
    ])
    expect(data.itemListElement.map((item) => item.position)).toEqual([1, 2])
    expect(data.itemListElement[1].item).toBe('https://heftra.com/privacy/')
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
