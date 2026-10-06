import { existsSync } from 'node:fs'
import sitemap from '@astrojs/sitemap'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig, envField } from 'astro/config'

const envFile = new URL('./.env', import.meta.url)

if (existsSync(envFile)) {
  process.loadEnvFile(envFile)
}

const siteUrl = process.env.PUBLIC_SITE_URL

if (!siteUrl) {
  throw new Error(
    'PUBLIC_SITE_URL is not set. Copy .env.example to .env or set it in the build environment.',
  )
}

export default defineConfig({
  site: siteUrl,
  output: 'static',
  compressHTML: true,
  trailingSlash: 'always',
  integrations: [
    sitemap({
      filter: (page) => !page.endsWith('/404/'),
      lastmod: new Date(),
    }),
  ],
  env: {
    schema: {
      PUBLIC_SITE_URL: envField.string({
        context: 'client',
        access: 'public',
        url: true,
      }),
      PUBLIC_APP_URL: envField.string({
        context: 'client',
        access: 'public',
        url: true,
      }),
      PUBLIC_API_URL: envField.string({
        context: 'client',
        access: 'public',
        url: true,
      }),
    },
  },
  vite: {
    plugins: [tailwindcss()],
  },
})
