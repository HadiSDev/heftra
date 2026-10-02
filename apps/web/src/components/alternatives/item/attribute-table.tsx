import { Badge } from '#/components/ui'
import type { AttributeComparison } from '#/lib/api/alternative-types'
import { VERDICT_LABELS, VERDICT_VARIANTS } from '#/lib/format/alternatives'

/** The item's key attributes beside the alternative's, each marked same, better or worse. */
export function AttributeTable({
  comparison,
}: {
  comparison: Array<AttributeComparison>
}) {
  if (comparison.length === 0) {
    return null
  }
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left text-xs text-muted-foreground">
          <th className="py-1.5 pr-3 font-medium">Attribute</th>
          <th className="py-1.5 pr-3 font-medium">Yours</th>
          <th className="py-1.5 pr-3 font-medium">Alternative</th>
          <th className="py-1.5 font-medium">
            <span className="sr-only">Verdict</span>
          </th>
        </tr>
      </thead>
      <tbody className="divide-y divide-border">
        {comparison.map((row) => (
          <tr key={row.name} title={row.reason || undefined}>
            <td className="py-1.5 pr-3 text-muted-foreground">
              {row.name.replace(/_/g, ' ')}
            </td>
            <td className="py-1.5 pr-3">{row.item}</td>
            <td className="py-1.5 pr-3">{row.candidate ?? '—'}</td>
            <td className="py-1.5 text-right">
              <Badge variant={VERDICT_VARIANTS[row.verdict]}>
                {VERDICT_LABELS[row.verdict]}
              </Badge>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
