import { describe, expect, it } from 'vitest'
import type { ReferenceImportRead } from '#/lib/api/admin-emission-factor-types'
import { importDuration, importOutcome } from './reference-imports'

const JOB: ReferenceImportRead = {
  id: 'j1',
  kind: 'price_index',
  status: 'succeeded',
  subject: 'CPIAUCSL',
  activate: false,
  requested_by: 'u1',
  requested_by_name: null,
  requested_at: '2026-09-27T10:00:00Z',
  started_at: '2026-09-27T10:00:00Z',
  finished_at: '2026-09-27T10:02:10Z',
  result: { months: 956, latest_month: '2026-08-01' },
  error: null,
}

describe('importOutcome', () => {
  it('describes a refreshed index', () => {
    expect(importOutcome(JOB)).toBe('956 months, latest Aug 2026')
  })

  it('gives a failure its error', () => {
    expect(
      importOutcome({ ...JOB, status: 'failed', result: null, error: 'boom' }),
    ).toBe('boom')
  })

  it('is empty while running', () => {
    expect(importOutcome({ ...JOB, status: 'running', result: null })).toBe('')
  })
})

describe('importDuration', () => {
  it('rounds to minutes from a minute up', () => {
    expect(importDuration(JOB)).toBe('2 min')
  })

  it('is null before the job has finished', () => {
    expect(importDuration({ ...JOB, finished_at: null })).toBeNull()
  })
})
