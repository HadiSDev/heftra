import { execFile } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { promisify } from 'node:util'
import { describe, expect, it } from 'vitest'

const run = promisify(execFile)
const projectRoot = fileURLToPath(new URL('../../', import.meta.url))

describe('build configuration', () => {
  it('fails a build without PUBLIC_SITE_URL and names the variable', async () => {
    const build = run(
      './node_modules/.bin/astro',
      ['build', '--outDir', 'node_modules/.cache/config-test-dist'],
      {
        cwd: projectRoot,
        env: { ...process.env, PUBLIC_SITE_URL: '' },
      },
    )
    await expect(build).rejects.toMatchObject({
      stderr: expect.stringContaining('PUBLIC_SITE_URL'),
    })
  }, 60_000)
})
