import { Leaf } from 'lucide-react'
import {
  Button,
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
  Progress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '#/components/ui'
import type { SectorCoverageRow } from '#/lib/api/admin-emission-factor-types'
import { formatCount } from '#/lib/format/format'

/** What happened when matching was asked for a company. */
export type MatchRequest =
  | { state: 'pending' }
  | { state: 'requested' }
  | { state: 'failed'; message: string }

export interface CoverageCardProps {
  rows: Array<SectorCoverageRow>
  requests?: Record<string, MatchRequest | undefined>
  /** Omit to show the coverage without a way to request matching. */
  onMatch?: (companyId: string) => void
}

function matchedShare(row: SectorCoverageRow): number {
  if (row.lines === 0) {
    return 0
  }
  return Math.round(((row.ai + row.human) / row.lines) * 100)
}

function RequestNote({ request }: { request: MatchRequest | undefined }) {
  if (request?.state === 'requested') {
    return <span className="text-xs text-success">Matching requested</span>
  }
  if (request?.state === 'failed') {
    return <span className="text-xs text-destructive">{request.message}</span>
  }
  return null
}

function spansOrganizations(rows: Array<SectorCoverageRow>): boolean {
  return new Set(rows.map((row) => row.organization_name)).size > 1
}

/** Each company's lines by emission sector, with a way to match the rest. */
export function CoverageCard({
  rows,
  requests = {},
  onMatch,
}: CoverageCardProps) {
  const showOrganization = spansOrganizations(rows)
  return (
    <Card role="region" aria-label="Sector coverage">
      <CardHeader>
        <CardTitle>Sector coverage</CardTitle>
        <CardDescription>
          Lines need an emission sector in the active set before they can be
          estimated.
        </CardDescription>
      </CardHeader>
      <div className="overflow-x-auto px-2 pb-2">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Company</TableHead>
              <TableHead className="w-40">Matched</TableHead>
              <TableHead className="text-right">AI</TableHead>
              <TableHead className="text-right">Person</TableHead>
              <TableHead className="text-right">To review</TableHead>
              <TableHead className="text-right">Unmatched</TableHead>
              {onMatch ? (
                <TableHead className="text-right">
                  <span className="sr-only">Actions</span>
                </TableHead>
              ) : null}
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => {
              const share = matchedShare(row)
              const request = requests[row.company_id]
              return (
                <TableRow key={row.company_id}>
                  <TableCell>
                    <div className="flex flex-col">
                      <span className="font-medium">{row.company_name}</span>
                      <span className="text-xs text-muted-foreground">
                        {showOrganization ? `${row.organization_name} · ` : ''}
                        {formatCount(row.lines)} lines
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Progress
                        aria-label={`${row.company_name}: ${share}% matched`}
                        value={share}
                        className="w-24"
                      />
                      <span className="text-xs tabular-nums">{share}%</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatCount(row.ai)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatCount(row.human)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {row.needs_review > 0 ? (
                      <span className="text-warning">
                        {formatCount(row.needs_review)}
                      </span>
                    ) : (
                      '0'
                    )}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatCount(row.unmatched)}
                  </TableCell>
                  {onMatch ? (
                    <TableCell className="text-right">
                      <div className="flex flex-col items-end gap-1">
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={
                            row.lines === 0 || request?.state === 'pending'
                          }
                          onClick={() => {
                            onMatch(row.company_id)
                          }}
                        >
                          <Leaf />
                          Match emission sectors
                        </Button>
                        <RequestNote request={request} />
                      </div>
                    </TableCell>
                  ) : null}
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>
    </Card>
  )
}
