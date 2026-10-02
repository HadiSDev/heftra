import * as React from 'react'
import { Check, Pencil, Quote, X } from 'lucide-react'
import { Badge, Button, Card, cn } from '#/components/ui'
import type { TermPatch, TermRead } from '#/lib/api/agreement-types'
import type { SpendCategoryRead } from '#/lib/api/types'
import { scopeCategoryPaths } from '#/lib/agreements/scope-categories'
import { termFields, termProblem, termValues } from '#/lib/agreements/term-form'
import type { TermFormValues } from '#/lib/agreements/term-form'
import { TERM_KIND_LABELS } from '#/lib/format/agreements'
import { toNumber } from '#/lib/format/format'
import { TermFieldsForm } from './term-fields-form'
import { TermSummary } from './term-summary'

const STATUS: Record<
  TermRead['status'],
  { label: string; variant: 'warning' | 'success' | 'outline' }
> = {
  draft: { label: 'To review', variant: 'warning' },
  confirmed: { label: 'Confirmed', variant: 'success' },
  rejected: { label: 'Rejected', variant: 'outline' },
}

export interface TermCardProps {
  term: TermRead
  /** The company's spend tree; null while it loads or when the company has none. */
  nodes: Array<SpendCategoryRead> | null
  canEdit: boolean
  busy: boolean
  onUpdate: (patch: TermPatch) => Promise<void>
  onShowPage: (page: number) => void
}

function ScopeCategories({
  term,
  nodes,
}: {
  term: TermRead
  nodes: Array<SpendCategoryRead>
}) {
  const paths = scopeCategoryPaths(nodes, term.scope_category_ids)
  return (
    <p className="text-xs text-muted-foreground">
      {paths.length > 0
        ? `Spend categories: ${paths.join(', ')}`
        : 'Spend categories: chosen at the next check'}
    </p>
  )
}

/** One term: what it says, the clause it came from, and its review controls. */
export function TermCard({
  term,
  nodes,
  canEdit,
  busy,
  onUpdate,
  onShowPage,
}: TermCardProps) {
  const [editing, setEditing] = React.useState<TermFormValues | null>(null)
  const [error, setError] = React.useState<string | null>(null)
  const status = STATUS[term.status]

  async function save(confirm: boolean) {
    if (!editing) {
      return
    }
    const problem = termProblem(term.kind, editing)
    if (problem) {
      setError(problem)
      return
    }
    const saved = await update({
      ...termFields(term.kind, editing),
      ...(confirm ? { status: 'confirmed' } : {}),
    })
    if (saved) {
      setEditing(null)
    }
  }

  async function update(patch: TermPatch): Promise<boolean> {
    setError(null)
    try {
      await onUpdate(patch)
      return true
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : 'Not saved')
      return false
    }
  }

  return (
    <Card
      role="article"
      aria-label={`${TERM_KIND_LABELS[term.kind]}: ${term.item ?? term.scope}`}
      className={cn(
        'flex flex-col gap-3 p-4',
        term.status === 'draft' && 'ring-1 ring-warning/40',
        term.status === 'rejected' && 'opacity-60',
      )}
    >
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="info">{TERM_KIND_LABELS[term.kind]}</Badge>
        <Badge variant={status.variant}>{status.label}</Badge>
        <span className="text-xs text-muted-foreground">
          {term.source === 'ai'
            ? `Read by AI${term.confidence !== null ? ` · ${Math.round(toNumber(term.confidence) * 100)}% sure` : ''}`
            : 'Added by a person'}
        </span>
      </div>

      {editing ? (
        <TermFieldsForm
          kind={term.kind}
          values={editing}
          onChange={setEditing}
          nodes={nodes}
        />
      ) : (
        <div className="flex flex-col gap-1 text-sm">
          <TermSummary term={term} />
          {nodes && nodes.length > 0 ? (
            <ScopeCategories term={term} nodes={nodes} />
          ) : null}
        </div>
      )}

      {term.quotes.length > 0 ? (
        <ul className="flex flex-col gap-1.5">
          {term.quotes.map((quote) => (
            <li key={`${quote.page}-${quote.text}`}>
              <button
                type="button"
                disabled={quote.page === null}
                onClick={() => {
                  if (quote.page !== null) {
                    onShowPage(quote.page)
                  }
                }}
                className="flex w-full gap-2 rounded-md border-l-2 border-border bg-muted/40 px-3 py-2 text-left text-xs text-muted-foreground outline-none transition hover:border-primary hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
              >
                <Quote className="size-3.5 shrink-0" aria-hidden="true" />
                <span className="flex-1 italic">{quote.text}</span>
                {quote.page !== null ? (
                  <span className="shrink-0 font-medium not-italic">
                    p. {quote.page}
                  </span>
                ) : null}
              </button>
            </li>
          ))}
        </ul>
      ) : null}

      {error ? <p className="text-sm text-destructive">{error}</p> : null}

      {canEdit ? (
        <div className="flex flex-wrap gap-2">
          {editing ? (
            <>
              <Button size="sm" disabled={busy} onClick={() => void save(true)}>
                <Check />
                Save and confirm
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={busy}
                onClick={() => void save(false)}
              >
                Save
              </Button>
              <Button
                size="sm"
                variant="ghost"
                disabled={busy}
                onClick={() => {
                  setEditing(null)
                  setError(null)
                }}
              >
                Cancel
              </Button>
            </>
          ) : (
            <>
              {term.status !== 'confirmed' ? (
                <Button
                  size="sm"
                  disabled={busy}
                  onClick={() => void update({ status: 'confirmed' })}
                >
                  <Check />
                  Confirm
                </Button>
              ) : null}
              <Button
                size="sm"
                variant="outline"
                disabled={busy}
                onClick={() => {
                  setEditing(termValues(term))
                }}
              >
                <Pencil />
                Edit
              </Button>
              {term.status !== 'rejected' ? (
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={busy}
                  onClick={() => void update({ status: 'rejected' })}
                >
                  <X />
                  Reject
                </Button>
              ) : null}
            </>
          )}
        </div>
      ) : null}
    </Card>
  )
}
