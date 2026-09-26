import * as React from 'react'
import {
  Button,
  Combobox,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxList,
  Field,
  FieldLabel,
} from '#/components/ui'
import { serverErrorMessage } from '#/lib/form-errors'
import type { EmissionSectorRead } from '#/lib/api/emission-types'
import type { InvoiceLineRead } from '#/lib/api/types'

/** The sector search the page runs for the picker. */
export interface SectorSearch {
  /** Whether emission factors are imported; undefined while that is not yet known. */
  available: boolean | undefined
  /** Sectors matching the latest search text; undefined while loading. */
  sectors: Array<EmissionSectorRead> | undefined
  onSearch: (text: string) => void
}

function SectorRow({ sector }: { sector: EmissionSectorRead }) {
  return (
    <span className="flex min-w-0 flex-1 items-center gap-2.5">
      <span className="min-w-0 truncate text-foreground">{sector.name}</span>
      <span className="shrink-0 font-mono text-xs text-muted-foreground">
        {sector.code}
      </span>
    </span>
  )
}

export interface EmissionSectorFieldProps {
  line: InvoiceLineRead
  search: SectorSearch
  /** Save the sector as a person's choice, or clear it with null. */
  onChoose: (sectorId: string | null) => Promise<void>
}

/** Choose which emission sector a line's spend is estimated with. */
export function EmissionSectorField({
  line,
  search,
  onChoose,
}: EmissionSectorFieldProps) {
  const current = line.emission_sector ?? null
  const [inputValue, setInputValue] = React.useState(current?.name ?? '')
  const [saving, setSaving] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    setInputValue(current?.name ?? '')
  }, [current?.name])

  async function choose(sectorId: string | null) {
    setSaving(true)
    setError(null)
    try {
      await onChoose(sectorId)
    } catch (failure) {
      setError(serverErrorMessage(failure))
    } finally {
      setSaving(false)
    }
  }

  if (search.available === false) {
    return (
      <Field>
        <FieldLabel>Emission sector</FieldLabel>
        <p className="text-sm text-muted-foreground">
          No emission factors are imported, so no sector can be chosen yet.
        </p>
      </Field>
    )
  }

  const items = search.sectors ?? []
  return (
    <Field>
      <FieldLabel>Emission sector</FieldLabel>
      <div className="flex items-center gap-2">
        <div className="min-w-0 flex-1">
          <Combobox
            items={items}
            filteredItems={items}
            value={current ?? undefined}
            inputValue={inputValue}
            disabled={saving || search.available === undefined}
            itemToStringLabel={(sector: EmissionSectorRead) => sector.name}
            isItemEqualToValue={(
              a: EmissionSectorRead,
              b: EmissionSectorRead,
            ) => a.id === b.id}
            onInputValueChange={(next: string) => {
              setInputValue(next)
              search.onSearch(next === current?.name ? '' : next)
            }}
            onValueChange={(next: EmissionSectorRead | null) => {
              if (next !== null && next.id !== current?.id) {
                void choose(next.id)
              }
            }}
          >
            <ComboboxInput
              aria-label="Emission sector"
              placeholder="Search sectors, such as hosting or air transport"
            />
            <ComboboxContent>
              <ComboboxEmpty>
                {search.sectors === undefined
                  ? 'Searching…'
                  : 'No sector matches that.'}
              </ComboboxEmpty>
              <ComboboxList>
                {(sector: EmissionSectorRead) => (
                  <ComboboxItem
                    key={sector.id}
                    value={sector}
                    aria-label={sector.name}
                    className="gap-0 py-2"
                  >
                    <SectorRow sector={sector} />
                  </ComboboxItem>
                )}
              </ComboboxList>
            </ComboboxContent>
          </Combobox>
        </div>
        {current !== null ? (
          <Button
            size="sm"
            variant="ghost"
            disabled={saving}
            onClick={() => void choose(null)}
          >
            Clear
          </Button>
        ) : null}
      </div>
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
    </Field>
  )
}
