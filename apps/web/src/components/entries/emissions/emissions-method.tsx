import { Tooltip, TooltipContent, TooltipTrigger } from '#/components/ui'
import type { FactorSetRead } from '#/lib/api/emission-types'
import { emissionsMethod, priceIndexCoverage } from '#/lib/format/emissions'

/** The method line: factor set, price year, and whether spend was adjusted for inflation. */
export function EmissionsMethod({ factorSet }: { factorSet: FactorSetRead }) {
  const method = emissionsMethod(factorSet)
  const coverage = priceIndexCoverage(factorSet)
  if (!coverage) {
    return <span>{method}</span>
  }
  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <span
            tabIndex={0}
            aria-label={`${method}. ${coverage}`}
            className="cursor-help underline decoration-dotted underline-offset-4"
          />
        }
      >
        {method}
      </TooltipTrigger>
      <TooltipContent className="max-w-80">{coverage}</TooltipContent>
    </Tooltip>
  )
}
