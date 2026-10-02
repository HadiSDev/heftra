import * as React from 'react'
import { FileWarning, Loader2, RotateCw } from 'lucide-react'
import { Button, Card } from '#/components/ui'
import type { PageRequest } from '#/components/entries/invoice-document/invoice-document'
import type {
  AgreementPatch,
  AgreementRead,
  TermCreate,
  TermPatch,
} from '#/lib/api/agreement-types'
import type { SpendCategoryRead, VendorRead } from '#/lib/api/types'
import { AddTermDialog } from './add-term-dialog'
import { AgreementDocument } from './agreement-document'
import { HeaderForm } from './header-form'
import { TermCard } from './term-card'

export interface TermsTabProps {
  agreement: AgreementRead
  canEdit: boolean
  vendors: Array<VendorRead>
  /** The company's spend tree; null while it loads or when the company has none. */
  spendTreeNodes: Array<SpendCategoryRead> | null
  onVendorSearch: (query: string) => void
  busyTermId: string | null
  onSaveHeader: (patch: AgreementPatch) => Promise<void>
  onUpdateTerm: (termId: string, patch: TermPatch) => Promise<void>
  onAddTerm: (term: TermCreate) => Promise<void>
  onReadAgain: () => void
}

function ReadingState({
  agreement,
  canEdit,
  onReadAgain,
}: {
  agreement: AgreementRead
  canEdit: boolean
  onReadAgain: () => void
}) {
  if (agreement.status === 'failed') {
    return (
      <Card className="flex flex-col items-start gap-3 p-5">
        <div className="flex items-center gap-2 font-medium text-destructive">
          <FileWarning className="size-5" aria-hidden="true" />
          The agreement couldn't be read
        </div>
        <p className="text-sm text-muted-foreground">{agreement.read_error}</p>
        {canEdit ? (
          <Button size="sm" variant="outline" onClick={onReadAgain}>
            <RotateCw />
            Read it again
          </Button>
        ) : null}
      </Card>
    )
  }
  return (
    <Card className="flex items-center gap-3 p-5 text-sm text-muted-foreground">
      <Loader2 className="size-5 animate-spin" aria-hidden="true" />
      Reading the agreement. Its terms appear here when it's done.
    </Card>
  )
}

/** The document beside its details and terms, for a person to review. */
export function TermsTab({
  agreement,
  canEdit,
  vendors,
  spendTreeNodes,
  onVendorSearch,
  busyTermId,
  onSaveHeader,
  onUpdateTerm,
  onAddTerm,
  onReadAgain,
}: TermsTabProps) {
  const [pageRequest, setPageRequest] = React.useState<PageRequest | null>(null)
  const reading = ['pending', 'reading', 'failed'].includes(agreement.status)
  const drafts = agreement.terms.filter(
    (term) => term.status === 'draft',
  ).length

  return (
    <div className="grid min-h-0 gap-6 lg:grid-cols-2">
      <Card className="h-[75vh] min-h-0 overflow-hidden p-0">
        <AgreementDocument
          agreementId={agreement.id}
          filename={agreement.file.filename}
          pageRequest={pageRequest}
        />
      </Card>
      <div className="flex min-w-0 flex-col gap-4">
        {reading ? (
          <ReadingState
            agreement={agreement}
            canEdit={canEdit}
            onReadAgain={onReadAgain}
          />
        ) : null}
        <HeaderForm
          key={agreement.read_at ?? agreement.id}
          agreement={agreement}
          vendors={vendors}
          onVendorSearch={onVendorSearch}
          canEdit={canEdit}
          onSave={onSaveHeader}
        />
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="font-display text-lg font-medium">
            Terms
            {drafts > 0 ? (
              <span className="ml-2 text-sm font-normal text-warning">
                {drafts} to review
              </span>
            ) : null}
          </h2>
          {canEdit && !reading ? (
            <AddTermDialog
              currency={agreement.currency}
              nodes={spendTreeNodes}
              onAdd={onAddTerm}
            />
          ) : null}
        </div>
        {!reading && agreement.terms.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No terms were found in this agreement. Add the ones it has.
          </p>
        ) : null}
        {agreement.terms.map((term) => (
          <TermCard
            key={term.id}
            term={term}
            nodes={spendTreeNodes}
            canEdit={canEdit}
            busy={busyTermId === term.id}
            onUpdate={(patch) => onUpdateTerm(term.id, patch)}
            onShowPage={(page) => {
              setPageRequest({ page })
            }}
          />
        ))}
      </div>
    </div>
  )
}
