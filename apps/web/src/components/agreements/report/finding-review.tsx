import * as React from 'react'
import {
  Button,
  Popover,
  PopoverContent,
  PopoverTitle,
  PopoverTrigger,
  Textarea,
} from '#/components/ui'
import type {
  FindingRead,
  FindingReview as Review,
} from '#/lib/api/agreement-types'

/** Accept a finding as an exception or rule it out of scope, with a note; or reopen it. */
export function FindingReview({
  finding,
  onReview,
}: {
  finding: FindingRead
  onReview: (review: Review) => Promise<void>
}) {
  const [open, setOpen] = React.useState(false)
  const [note, setNote] = React.useState(finding.review_note ?? '')
  const [busy, setBusy] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  async function review(status: Review['review_status']) {
    setBusy(true)
    setError(null)
    try {
      await onReview({ review_status: status, note: note.trim() || null })
      setOpen(false)
    } catch (reviewError) {
      setError(reviewError instanceof Error ? reviewError.message : 'Not saved')
    } finally {
      setBusy(false)
    }
  }

  if (finding.review_status !== 'open') {
    return (
      <Button
        size="sm"
        variant="ghost"
        disabled={busy}
        onClick={() => void review('open')}
      >
        Reopen
      </Button>
    )
  }
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger render={<Button size="sm" variant="outline" />}>
        Review
      </PopoverTrigger>
      <PopoverContent className="flex w-80 flex-col gap-3">
        <PopoverTitle className="text-sm font-medium">
          Review this finding
        </PopoverTitle>
        <Textarea
          rows={3}
          aria-label="Note"
          placeholder="Why, for whoever looks next (e.g. out of stock, urgent)"
          value={note}
          onChange={(event) => {
            setNote(event.target.value)
          }}
        />
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            disabled={busy}
            onClick={() => void review('exception')}
          >
            Accept as exception
          </Button>
          <Button
            size="sm"
            variant="outline"
            disabled={busy}
            onClick={() => void review('not_in_scope')}
          >
            Not in scope
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  )
}
