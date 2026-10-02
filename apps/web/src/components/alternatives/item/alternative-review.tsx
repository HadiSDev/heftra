import * as React from 'react'
import {
  Button,
  Popover,
  PopoverContent,
  PopoverTitle,
  PopoverTrigger,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Textarea,
} from '#/components/ui'
import type {
  AlternativeRead,
  AlternativeReview as Review,
  DismissReason,
} from '#/lib/api/alternative-types'
import { DISMISS_REASON_LABELS } from '#/lib/format/alternatives'

const REASONS = (
  Object.keys(DISMISS_REASON_LABELS) as Array<DismissReason>
).map((value) => ({ value, label: DISMISS_REASON_LABELS[value] }))

/** Dismiss an alternative with a reason and a note, mark that you switched, or reopen it. */
export function AlternativeReview({
  alternative,
  onReview,
}: {
  alternative: AlternativeRead
  onReview: (review: Review) => Promise<void>
}) {
  const [open, setOpen] = React.useState(false)
  const [reason, setReason] = React.useState<DismissReason>('not_equivalent')
  const [note, setNote] = React.useState('')
  const [busy, setBusy] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  async function review(next: Review) {
    setBusy(true)
    setError(null)
    try {
      await onReview(next)
      setOpen(false)
    } catch (reviewError) {
      setError(reviewError instanceof Error ? reviewError.message : 'Not saved')
    } finally {
      setBusy(false)
    }
  }

  if (alternative.review_status !== 'open') {
    return (
      <Button
        size="sm"
        variant="ghost"
        disabled={busy}
        onClick={() => void review({ review_status: 'open' })}
      >
        Reopen
      </Button>
    )
  }
  return (
    <div className="flex flex-wrap gap-2">
      <Button
        size="sm"
        variant="outline"
        disabled={busy}
        onClick={() => void review({ review_status: 'switched' })}
      >
        We switched
      </Button>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger render={<Button size="sm" variant="ghost" />}>
          Dismiss
        </PopoverTrigger>
        <PopoverContent className="flex w-80 flex-col gap-3">
          <PopoverTitle className="text-sm font-medium">
            Dismiss this alternative
          </PopoverTitle>
          <Select
            items={REASONS}
            value={reason}
            onValueChange={(next) => {
              setReason(next as DismissReason)
            }}
          >
            <SelectTrigger aria-label="Reason">
              <SelectValue items={REASONS} />
            </SelectTrigger>
            <SelectContent>
              {REASONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Textarea
            rows={3}
            aria-label="Note"
            placeholder="Why, for whoever looks next"
            value={note}
            onChange={(event) => {
              setNote(event.target.value)
            }}
          />
          {error ? <p className="text-sm text-destructive">{error}</p> : null}
          <Button
            size="sm"
            disabled={busy}
            onClick={() =>
              void review({
                review_status: 'dismissed',
                dismiss_reason: reason,
                note: note.trim() || null,
              })
            }
          >
            Dismiss
          </Button>
        </PopoverContent>
      </Popover>
      {error && !open ? (
        <p className="text-sm text-destructive">{error}</p>
      ) : null}
    </div>
  )
}
