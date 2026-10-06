import { getCollection } from 'astro:content'
import type { APIRoute } from 'astro'
import { site } from '../lib/site'

function byOrder<T extends { data: { order: number } }>(a: T, b: T): number {
  return a.data.order - b.data.order
}

export const GET: APIRoute = async ({ site: siteUrl }) => {
  const url = (path: string) => new URL(path, siteUrl).href
  const features = (await getCollection('features')).sort(byOrder)
  const integrations = (await getCollection('integrations')).sort(byOrder)
  const plans = (await getCollection('pricing')).sort(byOrder)
  const faq = (await getCollection('faq')).sort(byOrder)

  const euro = new Intl.NumberFormat('en-IE', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  })
  const priceOf = (monthly: number | null) =>
    monthly === null
      ? 'custom pricing'
      : `${euro.format(monthly)} per month, excl. VAT`

  const lines = [
    `# ${site.name}`,
    '',
    `> ${site.tagline} ${site.description}`,
    '',
    'Heftra is spend analytics software for mid-size and enterprise companies and groups in the EU, built for enterprise ERP systems. Data is hosted in the EU, and people review every AI decision.',
    '',
    '## Features',
    '',
    ...features.map(
      (feature) => `- **${feature.data.title}**: ${feature.data.benefit}`,
    ),
    '',
    '## ERP integrations',
    '',
    ...integrations.map(
      (integration) =>
        `- ${integration.data.name} (${integration.data.region}): ${integration.data.status === 'live' ? 'available' : 'coming soon'}`,
    ),
    '',
    '## Pricing',
    '',
    ...plans.map(
      (plan) =>
        `- **${plan.data.name}**: ${priceOf(plan.data.monthlyPriceEur)}. ${plan.data.audience}`,
    ),
    '',
    '## FAQ',
    '',
    ...faq.flatMap((entry) => [
      `### ${entry.data.question}`,
      '',
      entry.data.answer,
      '',
    ]),
    '## Links',
    '',
    `- [Home](${url('/')})`,
    `- [Get a demo](${url('/demo/')})`,
    `- [Privacy policy](${url('/privacy/')})`,
    `- [Terms of service](${url('/terms/')})`,
    `- Contact: ${site.contactEmail}`,
    '',
  ]

  return new Response(lines.join('\n'), {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  })
}
