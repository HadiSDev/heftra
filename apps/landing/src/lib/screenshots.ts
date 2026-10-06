import type { ImageMetadata } from 'astro'

export const screenshotNames = [
  'dashboard',
  'spend-lines',
  'alternatives',
  'agreements',
  'suppliers',
] as const

export type ScreenshotName = (typeof screenshotNames)[number]

const modules = import.meta.glob<{ default: ImageMetadata }>(
  '../assets/product/*.png',
  { eager: true },
)

export function screenshot(name: ScreenshotName): ImageMetadata | undefined {
  const module = modules[`../assets/product/${name}-dark.png`]
  if (!module) {
    return undefined
  }
  return module.default
}
