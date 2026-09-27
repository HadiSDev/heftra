import * as React from 'react'
import type { ReferenceImportRead } from '#/lib/api/admin-emission-factor-types'
import { isImportUnfinished } from '#/lib/api/admin-emission-factors'

/** Calls `onFinished` whenever a job seen queued or running is later seen finished. */
export function useImportFinished(
  jobs: Array<ReferenceImportRead> | undefined,
  onFinished: () => void,
) {
  const unfinished = React.useRef(new Set<string>())
  React.useEffect(() => {
    if (!jobs) {
      return
    }
    const finishedNow = jobs.some(
      (job) => unfinished.current.has(job.id) && !isImportUnfinished(job),
    )
    unfinished.current = new Set(
      jobs.filter(isImportUnfinished).map((job) => job.id),
    )
    if (finishedNow) {
      onFinished()
    }
  }, [jobs, onFinished])
}
