import * as React from 'react'
import { Plus } from 'lucide-react'
import {
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '#/components/ui'
import type { AgreementTermKind, TermCreate } from '#/lib/api/agreement-types'
import {
  EMPTY_TERM_VALUES,
  termFields,
  termProblem,
} from '#/lib/agreements/term-form'
import { TERM_KIND_LABELS } from '#/lib/format/agreements'
import { TermFieldsForm } from './term-fields-form'

const KINDS = (Object.keys(TERM_KIND_LABELS) as Array<AgreementTermKind>).map(
  (kind) => ({ value: kind, label: TERM_KIND_LABELS[kind] }),
)

/** Add a term the reader missed; it is confirmed as written. */
export function AddTermDialog({
  currency,
  onAdd,
}: {
  currency: string | null
  onAdd: (term: TermCreate) => Promise<void>
}) {
  const [open, setOpen] = React.useState(false)
  const [kind, setKind] =
    React.useState<AgreementTermKind>('preferred_supplier')
  const [values, setValues] = React.useState({
    ...EMPTY_TERM_VALUES,
    currency: currency ?? '',
  })
  const [error, setError] = React.useState<string | null>(null)
  const [busy, setBusy] = React.useState(false)

  async function add() {
    const problem = termProblem(kind, values)
    if (problem) {
      setError(problem)
      return
    }
    setBusy(true)
    try {
      await onAdd({ kind, ...termFields(kind, values) })
      setOpen(false)
      setValues({ ...EMPTY_TERM_VALUES, currency: currency ?? '' })
      setError(null)
    } catch (addError) {
      setError(addError instanceof Error ? addError.message : 'Not added')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button variant="outline" size="sm" />}>
        <Plus />
        Add a term
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add a term</DialogTitle>
          <DialogDescription>
            A term the reader missed. It counts as confirmed once added.
          </DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-4">
          <Select
            items={KINDS}
            value={kind}
            onValueChange={(next) => {
              setKind(next as AgreementTermKind)
            }}
          >
            <SelectTrigger aria-label="Kind of term">
              <SelectValue items={KINDS} />
            </SelectTrigger>
            <SelectContent>
              {KINDS.map((item) => (
                <SelectItem key={item.value} value={item.value}>
                  {item.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <TermFieldsForm kind={kind} values={values} onChange={setValues} />
          {error ? <p className="text-sm text-destructive">{error}</p> : null}
        </div>
        <DialogFooter>
          <Button
            variant="ghost"
            disabled={busy}
            onClick={() => {
              setOpen(false)
            }}
          >
            Cancel
          </Button>
          <Button disabled={busy} onClick={() => void add()}>
            {busy ? 'Adding…' : 'Add term'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
