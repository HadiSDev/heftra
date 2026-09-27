import type * as React from 'react'
import { Badge } from '#/components/ui'
import { calculationSteps, formatEmissions } from '#/lib/format/emissions'
import { toNumber } from '#/lib/format/format'
import type { InvoiceLineRead } from '#/lib/api/types'

const percent = new Intl.NumberFormat('en-GB', {
  style: 'percent',
  maximumFractionDigits: 0,
})

function Heading({ children }: { children: React.ReactNode }) {
  return (
    <h4 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
      {children}
    </h4>
  )
}

function WhySector({ line }: { line: InvoiceLineRead }) {
  if (line.emission_sector_source === 'human') {
    return <p className="text-sm text-muted-foreground">Chosen by a person.</p>
  }
  const confidence =
    line.emission_sector_confidence === null ||
    line.emission_sector_confidence === undefined
      ? null
      : percent.format(toNumber(line.emission_sector_confidence))
  return (
    <div className="flex flex-col gap-1.5">
      <p className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
        Matched by AI{confidence ? ` · ${confidence} sure` : ''}
        {line.emission_needs_review ? (
          <Badge variant="warning">Check sector</Badge>
        ) : null}
      </p>
      {line.emission_sector_rationale ? (
        <p className="rounded-md bg-muted px-3 py-2 text-sm text-muted-foreground">
          {line.emission_sector_rationale}
        </p>
      ) : null}
    </div>
  )
}

/** A line's emission sector, why it was chosen, and how its CO2e was worked out. */
export function LineEmissionsPanel({ line }: { line: InvoiceLineRead }) {
  const sector = line.emission_sector
  const calculation = line.emission_calculation
  return (
    <section
      aria-label="Emissions"
      className="flex flex-col gap-2 rounded-md border border-border px-3 py-3"
    >
      <Heading>Emissions</Heading>
      {sector ? (
        <>
          <p className="text-sm text-foreground">
            {sector.name}{' '}
            <span className="font-mono text-xs text-muted-foreground">
              {sector.code}
            </span>
          </p>
          <WhySector line={line} />
        </>
      ) : (
        <p className="text-sm text-muted-foreground">
          No emission sector yet. The next emissions run matches one, or a
          sector can be chosen below.
        </p>
      )}
      {calculation ? (
        <div className="flex flex-col gap-1">
          <Heading>Calculation</Heading>
          <ol className="flex flex-col gap-0.5 font-mono text-xs text-muted-foreground tabular-nums">
            {calculationSteps(calculation).map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
          <p className="text-sm font-medium text-foreground">
            {formatEmissions(calculation.kg_co2e)}
          </p>
        </div>
      ) : sector ? (
        <p className="text-sm text-muted-foreground">
          Not estimated: there is no factor for the supplier’s or the company’s
          country, or no exchange rate for the voucher’s date.
        </p>
      ) : null}
    </section>
  )
}
