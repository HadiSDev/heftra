import type { FindingRead } from '#/lib/api/agreement-types'

/** The findings grouped by the item bought, in the order they came. */
export function byItem(
  findings: Array<FindingRead>,
): Array<Array<FindingRead>> {
  const groups = new Map<string, Array<FindingRead>>()
  for (const finding of findings) {
    const group = groups.get(finding.invoice_line_id)
    if (group) {
      group.push(finding)
    } else {
      groups.set(finding.invoice_line_id, [finding])
    }
  }
  return [...groups.values()]
}
