import {
  Badge,
  Button,
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
  cn,
} from '#/components/ui'
import type { AdminFactorSetRead } from '#/lib/api/admin-emission-factor-types'
import { formatCount, formatDay } from '#/lib/format/format'

export interface FactorSetsCardProps {
  sets: Array<AdminFactorSetRead>
  onActivate: (set: AdminFactorSetRead) => void
}

/** Every imported factor set, the active one marked, the others activatable. */
export function FactorSetsCard({ sets, onActivate }: FactorSetsCardProps) {
  return (
    <Card role="region" aria-label="Factor sets">
      <CardHeader>
        <CardTitle>Factor sets</CardTitle>
        <CardDescription>
          Every estimate uses the active set. Switching changes every figure at
          once.
        </CardDescription>
      </CardHeader>
      {sets.length === 0 ? (
        <p className="px-6 pb-6 text-sm text-muted-foreground">
          No factor sets are imported yet. Upload an Open CEDA workbook below.
        </p>
      ) : (
        <div className="overflow-x-auto px-2 pb-2">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Release</TableHead>
                <TableHead>Prices</TableHead>
                <TableHead className="text-right">Sectors</TableHead>
                <TableHead className="text-right">Factors</TableHead>
                <TableHead>Imported</TableHead>
                <TableHead className="text-right">
                  <span className="sr-only">Actions</span>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sets.map((set) => (
                <TableRow
                  key={set.id}
                  className={cn(set.active && 'bg-primary/5')}
                >
                  <TableCell>
                    <div className="flex flex-col">
                      <span className="font-medium text-foreground">
                        {set.version}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {set.attribution} · {set.classification}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="whitespace-nowrap">
                    {set.price_year} {set.currency}, {set.price_basis}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatCount(set.sectors)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatCount(set.factors)}
                  </TableCell>
                  <TableCell className="whitespace-nowrap">
                    {formatDay(set.imported_at)}
                  </TableCell>
                  <TableCell className="text-right">
                    {set.active ? (
                      <Badge variant="success">Active</Badge>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          onActivate(set)
                        }}
                      >
                        Activate
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </Card>
  )
}
