import { X } from 'lucide-react'
import { TreeSelector } from '#/components/spend-tree/tree-selector'
import { formatPath } from '#/lib/api/spend-trees'
import type { SpendCategoryRead } from '#/lib/api/types'

export interface ScopeCategoriesFieldProps {
  nodes: Array<SpendCategoryRead>
  value: Array<string>
  onChange: (ids: Array<string>) => void
}

/** The spend categories a term covers: each one removable, and more added from the tree. */
export function ScopeCategoriesField({
  nodes,
  value,
  onChange,
}: ScopeCategoriesFieldProps) {
  const byId = new Map(nodes.map((node) => [node.id, node]))
  return (
    <div className="flex flex-col gap-2">
      {value.length > 0 ? (
        <ul className="flex flex-wrap gap-1.5" aria-label="Chosen categories">
          {value.map((id) => {
            const node = byId.get(id)
            const label = node
              ? formatPath(node)
              : 'A category no longer in the tree'
            return (
              <li
                key={id}
                className="flex items-center gap-1 rounded-md border border-border bg-muted/50 py-0.5 pr-0.5 pl-2 text-xs"
              >
                {label}
                <button
                  type="button"
                  aria-label={`Remove ${label}`}
                  onClick={() => {
                    onChange(value.filter((other) => other !== id))
                  }}
                  className="rounded p-0.5 text-muted-foreground hover:bg-muted hover:text-foreground"
                >
                  <X className="size-3.5" aria-hidden="true" />
                </button>
              </li>
            )
          })}
        </ul>
      ) : (
        <p className="text-xs text-muted-foreground">
          None chosen. The next check chooses them from what the term covers.
        </p>
      )}
      <TreeSelector
        nodes={nodes}
        value={null}
        placeholder="Add a category"
        onChange={(node) => {
          if (!value.includes(node.id)) {
            onChange([...value, node.id])
          }
        }}
      />
    </div>
  )
}
