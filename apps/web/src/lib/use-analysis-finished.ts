import * as React from 'react'
import type { AgreementRead } from '#/lib/api/agreement-types'
import { isAnalysing } from '#/lib/api/agreements'

/** Calls `onFinished` when an analysis seen queued or running is later seen finished. */
export function useAnalysisFinished(
  agreement: AgreementRead | undefined,
  onFinished: () => void,
) {
  const watching = React.useRef<string | null>(null)
  React.useEffect(() => {
    if (!agreement) {
      return
    }
    const analysis = agreement.analysis
    if (isAnalysing(agreement)) {
      watching.current = analysis?.id ?? null
      return
    }
    const finishedNow = watching.current !== null
    watching.current = null
    if (finishedNow) {
      onFinished()
    }
  }, [agreement, onFinished])
}
