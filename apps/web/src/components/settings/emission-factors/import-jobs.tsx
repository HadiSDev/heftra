import {
  Badge,
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '#/components/ui'
import type {
  ReferenceImportRead,
  ReferenceImportStatus,
} from '#/lib/api/admin-emission-factor-types'
import { formatRelativeTime } from '#/lib/format/format'
import {
  IMPORT_KIND_LABELS,
  importDuration,
  importOutcome,
} from '#/lib/format/reference-imports'

const STATUS_BADGES: Record<
  ReferenceImportStatus,
  { label: string; variant: 'default' | 'info' | 'success' | 'destructive' }
> = {
  queued: { label: 'Queued', variant: 'default' },
  running: { label: 'Running', variant: 'info' },
  succeeded: { label: 'Succeeded', variant: 'success' },
  failed: { label: 'Failed', variant: 'destructive' },
}

/** Recent workbook uploads and index refreshes, with their outcome. */
export function ImportJobs({ jobs }: { jobs: Array<ReferenceImportRead> }) {
  return (
    <Card role="region" aria-label="Recent imports">
      <CardHeader>
        <CardTitle>Recent imports</CardTitle>
        <CardDescription>
          Uploads and refreshes run in the background; this list updates while
          one is running.
        </CardDescription>
      </CardHeader>
      {jobs.length === 0 ? (
        <p className="px-6 pb-6 text-sm text-muted-foreground">
          Nothing has been imported from here yet.
        </p>
      ) : (
        <div className="overflow-x-auto px-2 pb-2">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>What</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Outcome</TableHead>
                <TableHead>Requested</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {jobs.map((job) => {
                const badge = STATUS_BADGES[job.status]
                const duration = importDuration(job)
                return (
                  <TableRow key={job.id}>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="font-medium">{job.subject}</span>
                        <span className="text-xs text-muted-foreground">
                          {IMPORT_KIND_LABELS[job.kind]}
                          {job.activate ? ' · activate when imported' : ''}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={badge.variant}>{badge.label}</Badge>
                    </TableCell>
                    <TableCell
                      className={
                        job.status === 'failed'
                          ? 'text-destructive'
                          : 'text-muted-foreground'
                      }
                    >
                      {importOutcome(job) || '—'}
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-muted-foreground">
                      {formatRelativeTime(job.requested_at)}
                      {job.requested_by_name
                        ? ` by ${job.requested_by_name}`
                        : ''}
                      {duration ? ` · took ${duration}` : ''}
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </div>
      )}
    </Card>
  )
}
