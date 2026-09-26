import { Tooltip, TooltipContent, TooltipTrigger } from '#/components/ui'
import { formatEmissions } from '#/lib/format/emissions'
import type { VoucherGroupRead } from '#/lib/api/types'
import { EMISSIONS_STATUS_REASON } from './status-labels'

function Explained({ text, reason }: { text: string; reason: string }) {
  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <span
            tabIndex={0}
            aria-label={`${text}. ${reason}.`}
            className="cursor-help underline decoration-dotted underline-offset-4"
          />
        }
      >
        {text}
      </TooltipTrigger>
      <TooltipContent>{reason}.</TooltipContent>
    </Tooltip>
  )
}

/** A voucher's estimated CO2e, marked when partial, with the reason when there is none. */
export function VoucherEmissions({ group }: { group: VoucherGroupRead }) {
  const status = group.emissions_status
  if (status === null || status === undefined) {
    return <span className="text-muted-foreground">—</span>
  }
  const reason = EMISSIONS_STATUS_REASON[status]
  if (group.kg_co2e === null || group.kg_co2e === undefined) {
    return (
      <span className="text-muted-foreground">
        <Explained text="—" reason={reason} />
      </span>
    )
  }
  const text = formatEmissions(group.kg_co2e)
  if (status === 'partial') {
    return (
      <span className="font-mono text-sm tabular-nums">
        <Explained text={`${text}*`} reason={reason} />
      </span>
    )
  }
  return <span className="font-mono text-sm tabular-nums">{text}</span>
}
