import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

export const distDir = fileURLToPath(new URL('../../dist/', import.meta.url))

export function readDist(path: string): string {
  const file = join(distDir, path)
  if (!existsSync(file)) {
    throw new Error(
      `${path} is missing from dist/. Run \`astro build\` before the build tests.`,
    )
  }
  return readFileSync(file, 'utf8')
}

export function distTextFiles(dir: string = distDir): Array<string> {
  return readdirSync(dir).flatMap((entry) => {
    const path = join(dir, entry)
    if (statSync(path).isDirectory()) {
      return distTextFiles(path)
    }
    return /\.(html|js|css|xml|txt)$/.test(entry) ? [path] : []
  })
}

export function hrefsOf(html: string): Array<string> {
  return Array.from(html.matchAll(/href="([^"]*)"/g), (match) => match[1])
}

export function anchorsWithText(html: string, text: string): Array<string> {
  const pattern = /<a\b[^>]*href="([^"]*)"[^>]*>([\s\S]*?)<\/a>/g
  return Array.from(html.matchAll(pattern))
    .filter((match) => match[2].replace(/<[^>]+>/g, '').trim() === text)
    .map((match) => match[1])
}
