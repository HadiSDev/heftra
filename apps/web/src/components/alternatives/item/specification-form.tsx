import * as React from 'react'
import { Plus } from 'lucide-react'
import {
  Button,
  Card,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '#/components/ui'
import type {
  ItemClass,
  PricingUnit,
  Specification,
} from '#/lib/api/alternative-types'
import {
  emptyAttribute,
  optionalText,
  parseNumber,
  specProblem,
  specToSend,
} from '#/lib/alternatives/spec-form'
import {
  CLASS_LABELS,
  PRICING_UNITS,
  unitLabel,
} from '#/lib/format/alternatives'
import { AttributeRow } from './attribute-row'

const CLASSES = (Object.keys(CLASS_LABELS) as Array<ItemClass>).map(
  (value) => ({ value, label: CLASS_LABELS[value] }),
)
const UNITS = PRICING_UNITS.map((value) => ({ value, label: unitLabel(value) }))

const BLANK: Specification = {
  item_class: 'finished_good',
  product_type: '',
  name: '',
  brand: null,
  model: null,
  part_number: null,
  gtin: null,
  attributes: [],
  pricing_unit: 'piece',
  units_per_line_unit: 1,
  confidence: 1,
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

export interface SpecificationFormProps {
  spec: Specification | null
  lineUnit: string | null
  onSave: (spec: Specification) => Promise<void>
  onCancel: () => void
}

/** Correct an item's specification; it is kept from then on and the item searched again. */
export function SpecificationForm({
  spec,
  lineUnit,
  onSave,
  onCancel,
}: SpecificationFormProps) {
  const [draft, setDraft] = React.useState<Specification>(spec ?? BLANK)
  const [error, setError] = React.useState<string | null>(null)
  const [busy, setBusy] = React.useState(false)

  function text(field: 'brand' | 'model' | 'part_number' | 'gtin') {
    return (event: React.ChangeEvent<HTMLInputElement>) => {
      setDraft({ ...draft, [field]: optionalText(event.target.value) })
    }
  }

  async function save() {
    const problem = specProblem(draft)
    if (problem) {
      setError(problem)
      return
    }
    setBusy(true)
    setError(null)
    try {
      await onSave({ ...specToSend(draft), confidence: 1 })
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'Not saved')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card className="flex flex-col gap-4 p-5">
      <h2 className="font-display text-base font-medium">
        Correct the specification
      </h2>
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Kind of item">
          <Select
            items={CLASSES}
            value={draft.item_class}
            onValueChange={(next) => {
              setDraft({ ...draft, item_class: next as ItemClass })
            }}
          >
            <SelectTrigger aria-label="Kind of item">
              <SelectValue items={CLASSES} />
            </SelectTrigger>
            <SelectContent>
              {CLASSES.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </Field>
        <Field label="Product type">
          <Input
            value={draft.product_type}
            placeholder="e.g. business laptop"
            onChange={(event) => {
              setDraft({ ...draft, product_type: event.target.value })
            }}
          />
        </Field>
        <Field label="Name">
          <Input
            value={draft.name}
            onChange={(event) => {
              setDraft({ ...draft, name: event.target.value })
            }}
          />
        </Field>
        <Field label="Brand">
          <Input value={draft.brand ?? ''} onChange={text('brand')} />
        </Field>
        <Field label="Model">
          <Input value={draft.model ?? ''} onChange={text('model')} />
        </Field>
        <Field label="Part number">
          <Input
            value={draft.part_number ?? ''}
            onChange={text('part_number')}
          />
        </Field>
        <Field label="EAN">
          <Input value={draft.gtin ?? ''} onChange={text('gtin')} />
        </Field>
        <Field label="Priced per">
          <Select
            items={UNITS}
            value={draft.pricing_unit}
            onValueChange={(next) => {
              setDraft({ ...draft, pricing_unit: next as PricingUnit })
            }}
          >
            <SelectTrigger aria-label="Priced per">
              <SelectValue items={UNITS} />
            </SelectTrigger>
            <SelectContent>
              {UNITS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </Field>
        <Field
          label={`${unitLabel(draft.pricing_unit)} per ${lineUnit ?? 'line unit'}`}
        >
          <Input
            inputMode="decimal"
            defaultValue={draft.units_per_line_unit ?? ''}
            onChange={(event) => {
              setDraft({
                ...draft,
                units_per_line_unit: parseNumber(event.target.value),
              })
            }}
          />
        </Field>
      </div>

      <div className="flex flex-col gap-2">
        <span className="text-xs font-medium text-muted-foreground">
          Key attributes: what an alternative must not have less of
        </span>
        {draft.attributes.map((attribute, index) => (
          <AttributeRow
            key={index}
            attribute={attribute}
            onChange={(changed) => {
              setDraft({
                ...draft,
                attributes: draft.attributes.map((entry, at) =>
                  at === index ? changed : entry,
                ),
              })
            }}
            onRemove={() => {
              setDraft({
                ...draft,
                attributes: draft.attributes.filter((_, at) => at !== index),
              })
            }}
          />
        ))}
        <div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              setDraft({
                ...draft,
                attributes: [...draft.attributes, emptyAttribute()],
              })
            }}
          >
            <Plus />
            Add an attribute
          </Button>
        </div>
      </div>

      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      <div className="flex flex-wrap gap-2">
        <Button disabled={busy} onClick={() => void save()}>
          {busy ? 'Saving…' : 'Save and search again'}
        </Button>
        <Button variant="ghost" disabled={busy} onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </Card>
  )
}
