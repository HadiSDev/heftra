import type { ReferenceImportRead } from '#/lib/api/admin-emission-factor-types'
import { formatCount } from './format'
import { formatIndexMonth } from './emissions'

function numberField(result: Record<string, unknown>, key: string): number {
  const value = result[key]
  return typeof value === 'number' ? value : 0
}

function textField(result: Record<string, unknown>, key: string): string {
  const value = result[key]
  return typeof value === 'string' ? value : ''
}

/** What a finished job did, or why it failed; empty while it hasn't finished. */
export function importOutcome(job: ReferenceImportRead): string {
  if (job.status === 'failed') {
    return job.error ?? 'Failed'
  }
  if (job.status !== 'succeeded' || !job.result) {
    return ''
  }
  const result = job.result
  if (job.kind === 'price_index') {
    const latest = textField(result, 'latest_month')
    return `${formatCount(numberField(result, 'months'))} months, latest ${latest ? formatIndexMonth(latest) : '—'}`
  }
  const activated = result.active === true ? ', active' : ''
  return `${textField(result, 'version')}: ${formatCount(numberField(result, 'sectors'))} sectors, ${formatCount(numberField(result, 'factors'))} factors${activated}`
}

/** How long a job ran, e.g. "8 s" or "2 min"; null before it has finished. */
export function importDuration(job: ReferenceImportRead): string | null {
  if (!job.started_at || !job.finished_at) {
    return null
  }
  const seconds = Math.max(
    0,
    Math.round(
      (new Date(job.finished_at).getTime() -
        new Date(job.started_at).getTime()) /
        1000,
    ),
  )
  if (seconds < 60) {
    return `${seconds} s`
  }
  return `${Math.round(seconds / 60)} min`
}

export const IMPORT_KIND_LABELS: Record<ReferenceImportRead['kind'], string> = {
  factor_workbook: 'Workbook',
  price_index: 'Price index',
}
