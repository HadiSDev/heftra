export interface FaqItem {
  question: string
  answer: string
}

export interface ParentOrganizationInput {
  legalName: string
  vatId: string
  streetAddress: string
  postalCode: string
  city: string
  countryCode: string
  email: string
  phone: string
  website: string
  sameAs: Array<string>
}

export interface OrganizationInput {
  name: string
  siteUrl: string
  logoUrl: string
  email: string
  parent: ParentOrganizationInput
}

export interface PricedPlan {
  name: string
  monthlyPriceEur: number
}

export interface SoftwareApplicationInput {
  name: string
  description: string
  siteUrl: string
  imageUrl: string
  plans: Array<PricedPlan>
}

export interface Breadcrumb {
  name: string
  url: string
}

const context = 'https://schema.org'

function organizationId(siteUrl: string): string {
  return `${siteUrl}#organization`
}

export function organizationJsonLd(input: OrganizationInput) {
  return {
    '@context': context,
    '@type': 'Organization',
    '@id': organizationId(input.siteUrl),
    name: input.name,
    url: input.siteUrl,
    logo: input.logoUrl,
    email: input.email,
    contactPoint: {
      '@type': 'ContactPoint',
      contactType: 'sales',
      email: input.email,
      areaServed: 'EU',
      availableLanguage: ['en', 'da'],
    },
    parentOrganization: {
      '@type': 'Organization',
      name: input.parent.legalName,
      legalName: input.parent.legalName,
      vatID: input.parent.vatId,
      url: input.parent.website,
      email: input.parent.email,
      telephone: input.parent.phone,
      sameAs: input.parent.sameAs,
      address: {
        '@type': 'PostalAddress',
        streetAddress: input.parent.streetAddress,
        postalCode: input.parent.postalCode,
        addressLocality: input.parent.city,
        addressCountry: input.parent.countryCode,
      },
    },
  }
}

export function websiteJsonLd(name: string, siteUrl: string) {
  return {
    '@context': context,
    '@type': 'WebSite',
    name,
    url: siteUrl,
    inLanguage: 'en',
    publisher: { '@id': organizationId(siteUrl) },
  }
}

export function softwareApplicationJsonLd(input: SoftwareApplicationInput) {
  return {
    '@context': context,
    '@type': 'SoftwareApplication',
    name: input.name,
    description: input.description,
    url: input.siteUrl,
    image: input.imageUrl,
    applicationCategory: 'BusinessApplication',
    applicationSubCategory: 'Spend analytics',
    operatingSystem: 'Web',
    publisher: { '@id': organizationId(input.siteUrl) },
    offers: input.plans.map((plan) => ({
      '@type': 'Offer',
      name: plan.name,
      price: plan.monthlyPriceEur.toFixed(2),
      priceCurrency: 'EUR',
      priceSpecification: {
        '@type': 'UnitPriceSpecification',
        price: plan.monthlyPriceEur.toFixed(2),
        priceCurrency: 'EUR',
        unitText: 'MONTH',
        valueAddedTaxIncluded: false,
      },
    })),
  }
}

export function breadcrumbJsonLd(items: Array<Breadcrumb>) {
  return {
    '@context': context,
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      item: item.url,
    })),
  }
}

export function faqPageJsonLd(items: Array<FaqItem>) {
  return {
    '@context': context,
    '@type': 'FAQPage',
    mainEntity: items.map((item) => ({
      '@type': 'Question',
      name: item.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: item.answer,
      },
    })),
  }
}

export function serializeJsonLd(data: object): string {
  return JSON.stringify(data).replace(/</g, '\\u003c')
}
