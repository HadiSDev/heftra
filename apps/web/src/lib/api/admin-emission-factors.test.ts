import { describe, expect, it, vi } from 'vitest'
import { QueryClient } from '@tanstack/react-query'
import type { ApiClient } from './api-client'
import type { ReferenceImportRead } from './admin-emission-factor-types'
import {
  IMPORT_POLL_INTERVAL_MS,
  hasUnfinishedImport,
  referenceImportsQueryOptions,
  uploadWorkbookMutation,
} from './admin-emission-factors'

function job(overrides: Partial<ReferenceImportRead>): ReferenceImportRead {
  return {
    id: 'j1',
    kind: 'price_index',
    status: 'succeeded',
    subject: 'CPIAUCSL',
    activate: false,
    requested_by: 'u1',
    requested_by_name: null,
    requested_at: '2026-09-27T10:00:00Z',
    started_at: null,
    finished_at: null,
    result: null,
    error: null,
    ...overrides,
  }
}

describe('hasUnfinishedImport', () => {
  it('looks only at jobs of the kind asked about', () => {
    const jobs = [job({ kind: 'factor_workbook', status: 'running' })]

    expect(hasUnfinishedImport(jobs, 'factor_workbook')).toBe(true)
    expect(hasUnfinishedImport(jobs, 'price_index')).toBe(false)
  })
})

describe('referenceImportsQueryOptions', () => {
  it('polls only while a job is unfinished', () => {
    const options = referenceImportsQueryOptions({} as ApiClient)
    const interval = options.refetchInterval as (query: {
      state: { data: Array<ReferenceImportRead> | undefined }
    }) => number | false

    expect(interval({ state: { data: [job({ status: 'queued' })] } })).toBe(
      IMPORT_POLL_INTERVAL_MS,
    )
    expect(interval({ state: { data: [job({})] } })).toBe(false)
  })
})

describe('uploadWorkbookMutation', () => {
  it('sends the file and the activate choice as a form', async () => {
    const upload = vi.fn(async () => job({ status: 'queued' }))
    const api = { upload } as unknown as ApiClient
    const options = uploadWorkbookMutation(api, new QueryClient())
    const file = new File(['PK'], 'ceda.xlsx')

    await options.mutationFn?.({ file, activate: true }, {} as never)

    const [path, form] = upload.mock.calls[0] as unknown as [string, FormData]
    expect(path).toBe('/api/v1/admin/emission-factors/workbooks')
    expect(form.get('file')).toBeInstanceOf(File)
    expect(form.get('activate')).toBe('true')
  })
})
