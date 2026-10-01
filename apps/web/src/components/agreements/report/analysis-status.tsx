import { CircleAlert, Loader2 } from 'lucide-react'
import type { AgreementRead } from '#/lib/api/agreement-types'
import { formatRelativeTime } from '#/lib/format/format'

function lastChecked(agreement: AgreementRead): string {
  return agreement.analysed_at
    ? `The figures below are from the check ${formatRelativeTime(agreement.analysed_at)}.`
    : 'Nothing has been checked yet.'
}

/** Whether the spend is being checked against the agreement, and how current the report is. */
export function AnalysisStatus({ agreement }: { agreement: AgreementRead }) {
  const analysis = agreement.analysis
  if (analysis?.status === 'queued' || analysis?.status === 'running') {
    const started = analysis.status === 'running' ? analysis.started_at : null
    return (
      <div role="status" className="flex items-start gap-2.5 text-sm">
        <Loader2
          className="mt-0.5 size-4 shrink-0 animate-spin text-primary"
          aria-hidden="true"
        />
        <p>
          <span className="font-medium">
            {started
              ? `Checking your spend against the agreement, started ${formatRelativeTime(started)}.`
              : 'Waiting for the worker to check your spend against the agreement.'}
          </span>{' '}
          <span className="text-muted-foreground">
            {lastChecked(agreement)}
          </span>
        </p>
      </div>
    )
  }
  if (analysis?.status === 'failed') {
    return (
      <div role="status" className="flex items-start gap-2.5 text-sm">
        <CircleAlert
          className="mt-0.5 size-4 shrink-0 text-destructive"
          aria-hidden="true"
        />
        <p>
          <span className="font-medium text-destructive">
            The last check didn’t finish
            {analysis.error ? `: ${analysis.error}` : ''}.
          </span>{' '}
          <span className="text-muted-foreground">
            {lastChecked(agreement)}
          </span>
        </p>
      </div>
    )
  }
  return (
    <p role="status" className="text-sm text-muted-foreground">
      {agreement.analysed_at
        ? `Checked ${formatRelativeTime(agreement.analysed_at)}.`
        : 'Not checked yet.'}
    </p>
  )
}
