import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  Button,
} from '#/components/ui'
import type { AdminFactorSetRead } from '#/lib/api/admin-emission-factor-types'

export interface ActivateDialogProps {
  target: AdminFactorSetRead | null
  current: AdminFactorSetRead | null
  busy: boolean
  error: string | null
  onClose: () => void
  onConfirm: () => void
}

/** Confirms switching the active factor set, naming both and what changes. */
export function ActivateDialog({
  target,
  current,
  busy,
  error,
  onClose,
  onConfirm,
}: ActivateDialogProps) {
  const rematch =
    target !== null &&
    current !== null &&
    target.classification !== current.classification
  return (
    <AlertDialog
      open={target !== null}
      onOpenChange={(open) => {
        if (!open) {
          onClose()
        }
      }}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Activate {target?.version}?</AlertDialogTitle>
          <AlertDialogDescription>
            {current
              ? `${current.version} is active now. `
              : 'No factor set is active now. '}
            Every emissions figure on the dashboard and in Spend Lines will be
            estimated with {target?.version} from its next load.
            {rematch
              ? ` It uses a different classification (${target.classification}), so every line will need matching to its sectors again.`
              : ''}
          </AlertDialogDescription>
        </AlertDialogHeader>
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        <AlertDialogFooter>
          <Button variant="ghost" onClick={onClose} disabled={busy}>
            Cancel
          </Button>
          <Button onClick={onConfirm} disabled={busy}>
            {busy ? 'Activating…' : `Activate ${target?.version ?? ''}`}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
