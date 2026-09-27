import * as React from 'react'
import {
  Button,
  Card,
  Combobox,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxList,
  DatePicker,
  Input,
} from '#/components/ui'
import type { AgreementPatch, AgreementRead } from '#/lib/api/agreement-types'
import type { VendorRead } from '#/lib/api/types'
import { fromIsoDate, toIsoDate } from '#/lib/format/format'

export interface HeaderFormProps {
  agreement: AgreementRead
  vendors: Array<VendorRead>
  onVendorSearch: (query: string) => void
  canEdit: boolean
  onSave: (patch: AgreementPatch) => Promise<void>
}

function Field({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      {children}
    </label>
  )
}

function linkedVendor(agreement: AgreementRead): VendorRead | undefined {
  if (!agreement.supplier) {
    return undefined
  }
  return {
    id: agreement.supplier.vendor_id,
    name: agreement.supplier.name,
    country_code: null,
    vat_number: null,
    description: null,
    website: null,
  }
}

/** The agreement's supplier, title, reference, dates and currency, as read and as corrected. */
export function HeaderForm({
  agreement,
  vendors,
  onVendorSearch,
  canEdit,
  onSave,
}: HeaderFormProps) {
  const [vendor, setVendor] = React.useState(linkedVendor(agreement))
  const [title, setTitle] = React.useState(agreement.title)
  const [reference, setReference] = React.useState(agreement.reference ?? '')
  const [startsOn, setStartsOn] = React.useState(
    fromIsoDate(agreement.starts_on),
  )
  const [endsOn, setEndsOn] = React.useState(fromIsoDate(agreement.ends_on))
  const [currency, setCurrency] = React.useState(agreement.currency ?? '')
  const [error, setError] = React.useState<string | null>(null)
  const [saving, setSaving] = React.useState(false)
  const options =
    vendor && !vendors.some((item) => item.id === vendor.id)
      ? [vendor, ...vendors]
      : vendors

  async function save(event: React.FormEvent) {
    event.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await onSave({
        vendor_id: vendor?.id ?? null,
        title: title.trim() || agreement.title,
        reference: reference.trim() || null,
        starts_on: toIsoDate(startsOn) ?? null,
        ends_on: toIsoDate(endsOn) ?? null,
        currency: currency.trim().toUpperCase() || null,
      })
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'Not saved')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card role="region" aria-label="Agreement details" className="p-4">
      <form
        className="flex flex-col gap-4"
        onSubmit={(event) => {
          void save(event)
        }}
      >
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Supplier">
            <Combobox
              items={options}
              value={vendor}
              disabled={!canEdit}
              itemToStringLabel={(item: VendorRead) => item.name}
              isItemEqualToValue={(a: VendorRead, b: VendorRead) =>
                a.id === b.id
              }
              onValueChange={(next: VendorRead | null) => {
                setVendor(next ?? undefined)
              }}
              onInputValueChange={onVendorSearch}
            >
              <ComboboxInput
                placeholder={agreement.supplier_name ?? 'Choose the supplier'}
                aria-label="Supplier"
              />
              <ComboboxContent>
                <ComboboxEmpty>No suppliers found.</ComboboxEmpty>
                <ComboboxList>
                  {(item: VendorRead) => (
                    <ComboboxItem key={item.id} value={item}>
                      {item.name}
                    </ComboboxItem>
                  )}
                </ComboboxList>
              </ComboboxContent>
            </Combobox>
          </Field>
          <Field label="Title">
            <Input
              value={title}
              disabled={!canEdit}
              onChange={(event) => {
                setTitle(event.target.value)
              }}
            />
          </Field>
          <Field label="Reference">
            <Input
              value={reference}
              disabled={!canEdit}
              onChange={(event) => {
                setReference(event.target.value)
              }}
            />
          </Field>
          <Field label="Currency">
            <Input
              value={currency}
              maxLength={3}
              disabled={!canEdit}
              onChange={(event) => {
                setCurrency(event.target.value)
              }}
            />
          </Field>
          <Field label="Starts">
            <DatePicker
              value={startsOn}
              onChange={setStartsOn}
              disabled={!canEdit}
              aria-label="Starts"
            />
          </Field>
          <Field label="Ends">
            <DatePicker
              value={endsOn}
              onChange={setEndsOn}
              disabled={!canEdit}
              placeholder="Open-ended"
              aria-label="Ends"
            />
          </Field>
        </div>
        {agreement.supplier_name && !agreement.supplier ? (
          <p className="text-xs text-muted-foreground">
            The agreement names {agreement.supplier_name}
            {agreement.supplier_vat_number
              ? ` (${agreement.supplier_vat_number})`
              : ''}
            , which isn't one of your suppliers yet. Pick the matching one.
          </p>
        ) : null}
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        {canEdit ? (
          <div>
            <Button type="submit" size="sm" disabled={saving}>
              {saving ? 'Saving…' : 'Save details'}
            </Button>
          </div>
        ) : null}
      </form>
    </Card>
  )
}
