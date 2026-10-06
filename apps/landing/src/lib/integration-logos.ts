import type { ImageMetadata } from 'astro'

const logos = import.meta.glob<{ default: ImageMetadata }>(
  '../assets/integrations/*.svg',
  { eager: true },
)

export function integrationLogo(logo: string): ImageMetadata {
  const module = logos[`../assets/integrations/${logo}.svg`]
  if (!module) {
    throw new Error(
      `No logo file src/assets/integrations/${logo}.svg for an integration.`,
    )
  }
  return module.default
}
