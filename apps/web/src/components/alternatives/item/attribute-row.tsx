import { Trash2 } from 'lucide-react'
import {
  IconButton,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '#/components/ui'
import type {
  Attribute,
  AttributeKind,
  Direction,
} from '#/lib/api/alternative-types'
import { optionalText, parseNumber } from '#/lib/alternatives/spec-form'

const KINDS: Array<{ value: AttributeKind; label: string }> = [
  { value: 'numeric', label: 'Number' },
  { value: 'tiered', label: 'Ranked part' },
  { value: 'other', label: 'Other' },
]

const DIRECTIONS: Array<{ value: Direction; label: string }> = [
  { value: 'more', label: 'More is better' },
  { value: 'less', label: 'Less is better' },
  { value: 'equal', label: 'Must be equal' },
]

function Choice<T extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: T
  options: Array<{ value: T; label: string }>
  onChange: (value: T) => void
}) {
  return (
    <Select
      items={options}
      value={value}
      onValueChange={(next) => {
        onChange(next as T)
      }}
    >
      <SelectTrigger aria-label={label}>
        <SelectValue items={options} />
      </SelectTrigger>
      <SelectContent>
        {options.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

/** One key attribute, edited by its kind: a number with its unit and direction, a ranked part
 * with its family, tier and generation, or a value. */
export function AttributeRow({
  attribute,
  onChange,
  onRemove,
}: {
  attribute: Attribute
  onChange: (attribute: Attribute) => void
  onRemove: () => void
}) {
  const label = attribute.name || 'attribute'
  return (
    <div className="flex flex-col gap-2 rounded-md border border-border p-3">
      <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_10rem_auto]">
        <Input
          aria-label="Attribute name"
          placeholder="Name, e.g. memory"
          value={attribute.name}
          onChange={(event) => {
            onChange({ ...attribute, name: event.target.value })
          }}
        />
        <Choice
          label={`Kind of ${label}`}
          value={attribute.kind}
          options={KINDS}
          onChange={(kind) => {
            onChange({ ...attribute, kind })
          }}
        />
        <IconButton
          aria-label={`Remove ${label}`}
          variant="ghost"
          onClick={onRemove}
        >
          <Trash2 />
        </IconButton>
      </div>
      {attribute.kind === 'numeric' ? (
        <div className="grid gap-2 sm:grid-cols-3">
          <Input
            aria-label={`${label} number`}
            inputMode="decimal"
            placeholder="Number"
            defaultValue={attribute.number ?? ''}
            onChange={(event) => {
              onChange({
                ...attribute,
                number: parseNumber(event.target.value),
              })
            }}
          />
          <Input
            aria-label={`${label} unit`}
            placeholder="Unit, e.g. GB"
            value={attribute.unit ?? ''}
            onChange={(event) => {
              onChange({ ...attribute, unit: optionalText(event.target.value) })
            }}
          />
          <Choice
            label={`${label} direction`}
            value={attribute.direction}
            options={DIRECTIONS}
            onChange={(direction) => {
              onChange({ ...attribute, direction })
            }}
          />
        </div>
      ) : (
        <Input
          aria-label={`${label} value`}
          placeholder={
            attribute.kind === 'tiered'
              ? 'As stated, e.g. Intel Core i7-1355U'
              : 'Value'
          }
          value={attribute.value}
          onChange={(event) => {
            onChange({ ...attribute, value: event.target.value })
          }}
        />
      )}
      {attribute.kind === 'tiered' ? (
        <div className="grid gap-2 sm:grid-cols-3">
          {(['family', 'tier', 'generation'] as const).map((field) => (
            <Input
              key={field}
              aria-label={`${label} ${field}`}
              placeholder={
                field === 'family'
                  ? 'Family, e.g. Intel Core'
                  : field === 'tier'
                    ? 'Tier, e.g. i7'
                    : 'Generation, e.g. 13'
              }
              value={attribute[field] ?? ''}
              onChange={(event) => {
                onChange({
                  ...attribute,
                  [field]: optionalText(event.target.value),
                })
              }}
            />
          ))}
        </div>
      ) : null}
    </div>
  )
}
