import * as React from 'react'
import { Link } from '@tanstack/react-router'
import { ArrowLeft, Trash2 } from 'lucide-react'
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  Button,
} from '#/components/ui'
import type { AgreementRead } from '#/lib/api/agreement-types'
import { formatDay } from '#/lib/format/format'
import { AgreementStatusBadge } from '../status-badge'
import { ReadAgainButton } from './read-again-button'

export interface AgreementHeadingProps {
  agreement: AgreementRead
  canEdit: boolean
  /** Whether this is the hosted demo, which hides actions it can't serve. */
  demo?: boolean
  onDelete: () => Promise<void>
  onReadAgain: () => Promise<void>
}

/** The agreement's title, supplier, validity and state, with a way back, a re-read and a delete. */
export function AgreementHeading({
  agreement,
  canEdit,
  demo = false,
  onDelete,
  onReadAgain,
}: AgreementHeadingProps) {
  const [confirming, setConfirming] = React.useState(false)
  const [busy, setBusy] = React.useState(false)
  const reading = ['pending', 'reading'].includes(agreement.status)
  const supplier = agreement.supplier?.name ?? agreement.supplier_name
  const validity = agreement.starts_on
    ? `${formatDay(agreement.starts_on)} – ${agreement.ends_on ? formatDay(agreement.ends_on) : 'open-ended'}`
    : null

  async function remove() {
    setBusy(true)
    try {
      await onDelete()
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <Link
        to="/agreements"
        className="inline-flex w-fit items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="size-4" aria-hidden="true" />
        Agreements
      </Link>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="font-display text-2xl font-semibold tracking-tight">
              {agreement.title}
            </h1>
            <AgreementStatusBadge agreement={agreement} />
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            {[supplier, agreement.reference, validity]
              .filter(Boolean)
              .join(' · ') || 'Details still to be read'}
          </p>
          {agreement.summary ? (
            <p className="mt-2 max-w-3xl text-sm">{agreement.summary}</p>
          ) : null}
        </div>
        {canEdit && !demo ? (
          <div className="flex items-center gap-2">
            {reading ? null : (
              <ReadAgainButton
                title={agreement.title}
                onReadAgain={onReadAgain}
              />
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setConfirming(true)
              }}
            >
              <Trash2 />
              Delete
            </Button>
          </div>
        ) : null}
      </div>
      <AlertDialog open={confirming} onOpenChange={setConfirming}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete {agreement.title}?</AlertDialogTitle>
            <AlertDialogDescription>
              Its document, terms and every finding against it are deleted. Your
              spend is not touched.
            </AlertDialogDescription>
          </AlertDialogHeader>
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
            <Button
              variant="destructive"
              disabled={busy}
              onClick={() => void remove()}
            >
              {busy ? 'Deleting…' : 'Delete agreement'}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
