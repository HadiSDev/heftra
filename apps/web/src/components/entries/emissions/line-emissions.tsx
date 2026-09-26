import { Badge, Tooltip, TooltipContent, TooltipTrigger } from '#/components/ui'
import { formatEmissions } from '#/lib/format/emissions'
import { toNumber } from '#/lib/format/format'
import type { InvoiceLineRead } from '#/lib/api/types'

const percent = new Intl.NumberFormat('en-GB', {
  style: 'percent',
  maximumFractionDigits: 0,
})

/** Who chose the sector and why, and whose factor was used. */
function explanation(line: InvoiceLineRead): string {
  const sector = line.emission_sector
  const parts = [sector ? `${sector.code} ${sector.name}.` : '']
  if (line.emission_sector_source === 'human') {
    parts.push('Chosen by a person.')
  } else {
    const confidence =
      line.emission_sector_confidence === null ||
      line.emission_sector_confidence === undefined
        ? ''
        : ` (${percent.format(toNumber(line.emission_sector_confidence))} sure)`
    parts.push(`Matched by AI${confidence}.`)
    if (line.emission_sector_rationale) {
      parts.push(line.emission_sector_rationale)
    }
  }
  if (line.emission_area) {
    parts.push(`Factor for ${line.emission_area}.`)
  }
  return parts.filter(Boolean).join(' ')
}

/** The emission sector a line was matched to, who chose it, and whether it needs a look. */
export function LineSector({ line }: { line: InvoiceLineRead }) {
  const sector = line.emission_sector
  if (!sector) {
    return null
  }
  const source = line.emission_sector_source === 'human' ? 'person' : 'AI'
  const detail = explanation(line)
  return (
    <span className="mt-1 flex min-w-0 flex-wrap items-center gap-1 text-xs text-muted-foreground">
      <Tooltip>
        <TooltipTrigger
          render={
            <span
              tabIndex={0}
              aria-label={`Emission sector: ${detail}`}
              className="min-w-0 cursor-help truncate"
            />
          }
        >
          {sector.name}
        </TooltipTrigger>
        <TooltipContent className="max-w-80">{detail}</TooltipContent>
      </Tooltip>
      <span className="rounded border border-border px-1 text-[10px] leading-4">
        {source}
      </span>
      {line.emission_needs_review ? (
        <Badge variant="warning">Check sector</Badge>
      ) : null}
    </span>
  )
}

/** A line's estimated CO2e, or a dash when it has none. */
export function LineEmissions({ line }: { line: InvoiceLineRead }) {
  if (line.kg_co2e === null || line.kg_co2e === undefined) {
    return <span className="text-muted-foreground">—</span>
  }
  return (
    <span className="font-mono text-sm tabular-nums text-muted-foreground">
      {formatEmissions(line.kg_co2e)}
    </span>
  )
}
