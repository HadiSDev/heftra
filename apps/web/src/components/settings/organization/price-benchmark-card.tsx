import * as React from 'react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Switch,
} from '#/components/ui'
import { serverErrorMessage } from '#/lib/form-errors'

export interface PriceBenchmarkCardProps {
  enabled: boolean
  /** Whether the caller may change it: organization admins only. */
  canManage: boolean
  onChange: (enabled: boolean) => Promise<unknown>
}

/** Whether the organization shares its prices, anonymously, and sees what others pay. */
export function PriceBenchmarkCard({
  enabled,
  canManage,
  onChange,
}: PriceBenchmarkCardProps) {
  const [busy, setBusy] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  async function change(next: boolean) {
    setBusy(true)
    setError(null)
    try {
      await onChange(next)
    } catch (changeError) {
      setError(serverErrorMessage(changeError))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Price benchmark</CardTitle>
        <CardDescription>
          Compare what you pay with what other organizations on Spendyard pay
          for the same products and specifications.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4 text-sm">
        <label className="flex items-center justify-between gap-4">
          <span className="font-medium">Take part in the price benchmark</span>
          <Switch
            checked={enabled}
            disabled={!canManage || busy}
            onCheckedChange={(next) => void change(next)}
            aria-label="Take part in the price benchmark"
          />
        </label>
        <ul className="flex list-disc flex-col gap-1 pl-5 text-muted-foreground">
          <li>
            You share your prices per unit only, never your name, your companies
            or your suppliers.
          </li>
          <li>
            A price is shown only as the median and the cheapest quarter of at
            least three other organizations.
          </li>
          <li>
            {enabled
              ? 'Your items get alternatives from other customers’ prices.'
              : 'While this is off, your prices are left out and your items get no alternatives from other customers’ prices.'}
          </li>
        </ul>
        {!canManage ? (
          <p className="text-xs text-muted-foreground">
            Only an organization admin can change this.
          </p>
        ) : null}
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
      </CardContent>
    </Card>
  )
}
