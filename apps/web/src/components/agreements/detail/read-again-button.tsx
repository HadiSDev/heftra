import * as React from 'react'
import { RotateCw } from 'lucide-react'
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  Button,
} from '#/components/ui'

export interface ReadAgainButtonProps {
  title: string
  onReadAgain: () => Promise<void>
}

/** Queue the agreement to be read again, once the manager has confirmed it. */
export function ReadAgainButton({ title, onReadAgain }: ReadAgainButtonProps) {
  const [confirming, setConfirming] = React.useState(false)
  const [busy, setBusy] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  async function readAgain() {
    setBusy(true)
    setError(null)
    try {
      await onReadAgain()
      setConfirming(false)
    } catch (readError) {
      setError(readError instanceof Error ? readError.message : 'Not queued')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => {
          setError(null)
          setConfirming(true)
        }}
      >
        <RotateCw />
        Read again
      </Button>
      <AlertDialog open={confirming} onOpenChange={setConfirming}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Read {title} again?</AlertDialogTitle>
            <AlertDialogDescription>
              The document is read from the start. Terms still in draft are
              replaced by the new reading; terms you confirmed or rejected are
              kept.
            </AlertDialogDescription>
          </AlertDialogHeader>
          {error ? (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          ) : null}
          <AlertDialogFooter>
            <Button
              variant="ghost"
              disabled={busy}
              onClick={() => {
                setConfirming(false)
              }}
            >
              Cancel
            </Button>
            <Button disabled={busy} onClick={() => void readAgain()}>
              {busy ? 'Queuing…' : 'Read again'}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
