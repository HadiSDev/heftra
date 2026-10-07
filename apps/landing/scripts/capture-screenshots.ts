import { mkdirSync } from 'node:fs'
import { chromium } from '@playwright/test'
import type { Page } from '@playwright/test'
import { applyPersona, hideDevelopmentOverlays } from './capture/scrub.ts'
import type { Persona } from './capture/scrub.ts'
import { signIn, signInFromEnv } from './capture/sign-in.ts'

interface Capture {
  name: string
  path: string
  waitFor: string
}

const captures: Array<Capture> = [
  { name: 'dashboard', path: '/', waitFor: 'main' },
  { name: 'spend-lines', path: '/invoice-lines', waitFor: 'table' },
  { name: 'alternatives', path: '/alternatives', waitFor: 'table' },
  {
    name: 'agreements',
    path: process.env.CAPTURE_AGREEMENT_PATH ?? '/agreements',
    waitFor: 'main',
  },
  { name: 'suppliers', path: '/suppliers', waitFor: 'table' },
]

const themes = ['dark'] as const

const appUrl = process.env.CAPTURE_APP_URL ?? 'http://localhost:3100'
const companyId = process.env.CAPTURE_COMPANY_ID
const persona: Persona = {
  personName: process.env.CAPTURE_PERSON_NAME ?? 'Mette Hansen',
  organizationName: process.env.CAPTURE_ORGANIZATION_NAME ?? 'Nordlys Byg',
}
const outputDir = new URL('../src/assets/product/', import.meta.url)

function pageUrl(path: string): string {
  const url = new URL(path, appUrl)
  if (companyId) {
    url.searchParams.set('company_id', companyId)
  }
  return url.href
}

async function applyTheme(
  page: Page,
  theme: (typeof themes)[number],
): Promise<void> {
  await page.emulateMedia({ colorScheme: theme })
  await page.evaluate((value) => {
    document.documentElement.classList.toggle('dark', value === 'dark')
  }, theme)
}

async function main(): Promise<void> {
  const method = signInFromEnv(process.env)
  mkdirSync(outputDir, { recursive: true })

  const browser = await chromium.launch()
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
  })
  const page = await context.newPage()
  await signIn(page, method, appUrl)

  for (const capture of captures) {
    await page.goto(pageUrl(capture.path))
    await page.waitForSelector(capture.waitFor)
    await page.waitForLoadState('networkidle')
    for (const theme of themes) {
      await applyTheme(page, theme)
      await hideDevelopmentOverlays(page)
      await applyPersona(page, persona)
      await page.waitForTimeout(300)
      const file = new URL(`${capture.name}-${theme}.png`, outputDir)
      await page.screenshot({ path: file.pathname })
      console.log(`captured ${capture.name} (${theme})`)
    }
  }

  await browser.close()
}

await main()
