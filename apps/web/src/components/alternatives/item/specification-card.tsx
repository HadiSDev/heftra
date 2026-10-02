import type * as React from 'react'
import { Badge, Card } from '#/components/ui'
import type { Attribute, ItemRead } from '#/lib/api/alternative-types'
import { CLASS_LABELS, unitLabel } from '#/lib/format/alternatives'

function attributeText(attribute: Attribute): string {
  if (attribute.kind === 'numeric' && attribute.number !== null) {
    const direction =
      attribute.direction === 'more'
        ? 'or more'
        : attribute.direction === 'less'
          ? 'or less'
          : 'exactly'
    return `${attribute.number} ${attribute.unit ?? ''} ${direction}`.replace(
      /\s+/g,
      ' ',
    )
  }
  return attribute.value
}

function Row({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="grid grid-cols-[9rem_minmax(0,1fr)] gap-3 py-1.5 text-sm">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="min-w-0 break-words">{children}</dd>
    </div>
  )
}

/** What the item is, as compared: its class, identifiers, key attributes and pricing unit. */
export function SpecificationCard({ item }: { item: ItemRead }) {
  const spec = item.spec
  if (!spec) {
    return (
      <Card className="p-5 text-sm text-muted-foreground">
        The specification hasn’t been read yet. It is read when the item is
        first searched.
      </Card>
    )
  }
  const identity = [spec.brand, spec.model, spec.part_number, spec.gtin]
    .filter(Boolean)
    .join(' · ')
  return (
    <Card className="flex flex-col gap-3 p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-display text-base font-medium">Specification</h2>
        <span className="text-xs text-muted-foreground">
          {item.spec_source === 'human'
            ? 'Set by a person'
            : `Read by AI · ${Math.round(spec.confidence * 100)}% sure`}
        </span>
      </div>
      <dl className="divide-y divide-border">
        <Row label="Kind">
          <span className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">{CLASS_LABELS[spec.item_class]}</Badge>
            {spec.product_type}
          </span>
        </Row>
        {identity ? <Row label="Identifiers">{identity}</Row> : null}
        <Row label="Priced per">
          {unitLabel(spec.pricing_unit)}
          {spec.units_per_line_unit !== null && item.unit
            ? ` · ${spec.units_per_line_unit} per ${item.unit}`
            : ''}
        </Row>
        {spec.attributes.map((attribute) => (
          <Row key={attribute.name} label={attribute.name.replace(/_/g, ' ')}>
            {attributeText(attribute)}
          </Row>
        ))}
      </dl>
    </Card>
  )
}
