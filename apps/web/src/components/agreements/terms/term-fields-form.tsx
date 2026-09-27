import {
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Textarea,
  cn,
} from '#/components/ui'
import type { AgreementTermKind } from '#/lib/api/agreement-types'
import type { TermFormValues } from '#/lib/agreements/term-form'

const PERIODS = [
  { value: 'month', label: 'Per month' },
  { value: 'quarter', label: 'Per quarter' },
  { value: 'year', label: 'Per year' },
  { value: 'agreement', label: 'Over the whole agreement' },
]

function Field({
  label,
  children,
  wide = false,
}: {
  label: string
  children: React.ReactNode
  wide?: boolean
}) {
  return (
    <label className={cn('flex flex-col gap-1.5', wide && 'sm:col-span-2')}>
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      {children}
    </label>
  )
}

export interface TermFieldsFormProps {
  kind: AgreementTermKind
  values: TermFormValues
  onChange: (values: TermFormValues) => void
}

/** The fields a term of `kind` has, as editable inputs. */
export function TermFieldsForm({
  kind,
  values,
  onChange,
}: TermFieldsFormProps) {
  function set(field: keyof TermFormValues) {
    return (
      event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
    ) => {
      onChange({ ...values, [field]: event.target.value })
    }
  }
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <Field label="Covers" wide>
        <Input value={values.scope} onChange={set('scope')} />
      </Field>
      {kind === 'preferred_supplier' ? (
        <Field label="Conditions" wide>
          <Input
            value={values.conditions}
            onChange={set('conditions')}
            placeholder="e.g. when available from stock"
          />
        </Field>
      ) : null}
      {kind === 'agreed_price' ? (
        <>
          <Field label="Item" wide>
            <Input
              value={values.item}
              onChange={set('item')}
              placeholder="Make, model or product number"
            />
          </Field>
          <Field label="Price">
            <Input
              inputMode="decimal"
              value={values.unit_price}
              onChange={set('unit_price')}
            />
          </Field>
          <Field label="Per">
            <Input
              value={values.unit}
              onChange={set('unit')}
              placeholder="unit"
            />
          </Field>
        </>
      ) : null}
      {kind === 'discount' ? (
        <Field label="Discount (%)">
          <Input
            inputMode="decimal"
            value={values.discount_percent}
            onChange={set('discount_percent')}
          />
        </Field>
      ) : null}
      {kind === 'volume_commitment' ? (
        <>
          <Field label="Committed amount">
            <Input
              inputMode="decimal"
              value={values.commitment_amount}
              onChange={set('commitment_amount')}
            />
          </Field>
          <Field label="Period">
            <Select
              items={PERIODS}
              value={values.commitment_period}
              onValueChange={(next) => {
                onChange({ ...values, commitment_period: String(next) })
              }}
            >
              <SelectTrigger aria-label="Period">
                <SelectValue items={PERIODS} />
              </SelectTrigger>
              <SelectContent>
                {PERIODS.map((period) => (
                  <SelectItem key={period.value} value={period.value}>
                    {period.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>
          <Field label="Rebate tiers (one per line: amount = rebate %)" wide>
            <Textarea
              rows={3}
              value={values.tiers}
              onChange={set('tiers')}
              placeholder={'100000 = 1%\n400000 = 2%'}
            />
          </Field>
        </>
      ) : null}
      {kind !== 'preferred_supplier' ? (
        <Field label="Currency">
          <Input
            value={values.currency}
            onChange={set('currency')}
            maxLength={3}
            placeholder="DKK"
          />
        </Field>
      ) : null}
    </div>
  )
}
