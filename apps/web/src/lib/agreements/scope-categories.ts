import { formatPath } from '#/lib/api/spend-trees'
import type { SpendCategoryRead } from '#/lib/api/types'

/** The paths of the categories a term covers, for reading. */
export function scopeCategoryPaths(
  nodes: Array<SpendCategoryRead>,
  ids: Array<string>,
): Array<string> {
  const byId = new Map(nodes.map((node) => [node.id, node]))
  return ids
    .map((id) => byId.get(id))
    .filter((node): node is SpendCategoryRead => node !== undefined)
    .map((node) => formatPath(node))
}
