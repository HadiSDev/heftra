import { defineCollection } from 'astro:content'
import { file } from 'astro/loaders'
import { z } from 'astro/zod'
import { screenshotNames } from './lib/screenshots'
import { icons } from './components/ui/icons'

const iconName = z.enum(
  Object.keys(icons) as [keyof typeof icons, ...Array<keyof typeof icons>],
)

const features = defineCollection({
  loader: file('src/content/features.yaml'),
  schema: z.object({
    order: z.number().int(),
    icon: iconName,
    eyebrow: z.string().min(1),
    title: z.string().min(1),
    benefit: z.string().min(1),
    points: z.array(z.string().min(1)).min(2).max(4),
    screenshot: z.enum(screenshotNames),
    screenshotAlt: z.string().min(1),
  }),
})

const integrations = defineCollection({
  loader: file('src/content/integrations.yaml'),
  schema: z.object({
    order: z.number().int(),
    name: z.string().min(1),
    region: z.string().min(1),
    status: z.enum(['live', 'coming-soon']),
    logo: z.string().min(1),
    logoColor: z
      .string()
      .regex(/^#[0-9a-fA-F]{6}$/)
      .optional(),
    logoStyle: z.enum(['wordmark', 'icon']).default('wordmark'),
  }),
})

const outcomes = defineCollection({
  loader: file('src/content/outcomes.yaml'),
  schema: z.object({
    order: z.number().int(),
    value: z.number(),
    prefix: z.string().default(''),
    suffix: z.string().default(''),
    label: z.string().min(1),
    source: z.string().min(1),
    draft: z.boolean().default(false),
  }),
})

const pricing = defineCollection({
  loader: file('src/content/pricing.yaml'),
  schema: z.object({
    order: z.number().int(),
    name: z.string().min(1),
    audience: z.string().min(1),
    monthlyPriceEur: z.number().positive().nullable(),
    annualMonthlyPriceEur: z.number().positive().nullable(),
    recommended: z.boolean().default(false),
    ctaLabel: z.string().min(1),
    includesFrom: z.string().optional(),
    features: z.array(z.string().min(1)).min(1),
  }),
})

const faq = defineCollection({
  loader: file('src/content/faq.yaml'),
  schema: z.object({
    order: z.number().int(),
    question: z.string().min(1),
    answer: z.string().min(1),
  }),
})

const testimonials = defineCollection({
  loader: file('src/content/testimonials.yaml'),
  schema: z.object({
    order: z.number().int(),
    quote: z.string().min(1),
    name: z.string().min(1),
    role: z.string().min(1),
    company: z.string().min(1),
  }),
})

export const collections = {
  features,
  integrations,
  outcomes,
  pricing,
  faq,
  testimonials,
}
