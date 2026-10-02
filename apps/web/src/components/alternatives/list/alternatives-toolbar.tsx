import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '#/components/ui'
import type {
  AlternativeFilters,
  AlternativeMatch,
  AlternativeSource,
  ItemClass,
} from '#/lib/api/alternative-types'
import type { CompanyRead } from '#/lib/api/types'
import {
  CLASS_LABELS,
  MATCH_LABELS,
  SOURCE_LABELS,
} from '#/lib/format/alternatives'

const ALL = '__all__'

function FilterSelect({
  label,
  value,
  allLabel,
  options,
  onChange,
}: {
  label: string
  value: string | undefined
  allLabel: string
  options: Array<{ value: string; label: string }>
  onChange: (value: string | undefined) => void
}) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <Select
        value={value ?? ''}
        onValueChange={(next: string | null) => {
          onChange(next && next !== ALL ? next : undefined)
        }}
      >
        <SelectTrigger className="w-48" aria-label={label}>
          <SelectValue placeholder={allLabel} items={options} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>{allLabel}</SelectItem>
          {options.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </label>
  )
}

function entries<T extends string>(labels: Record<T, string>) {
  return (Object.keys(labels) as Array<T>).map((value) => ({
    value,
    label: labels[value],
  }))
}

export interface AlternativesToolbarProps {
  filters: AlternativeFilters
  companies: Array<CompanyRead>
  onChange: (changes: Partial<AlternativeFilters>) => void
}

/** Narrow the list to a company, a source, a kind of match or a class of item. */
export function AlternativesToolbar({
  filters,
  companies,
  onChange,
}: AlternativesToolbarProps) {
  return (
    <div className="flex flex-wrap items-end gap-3">
      <FilterSelect
        label="Company"
        value={filters.company_id}
        allLabel="All companies"
        options={companies.map((company) => ({
          value: company.id,
          label: company.name,
        }))}
        onChange={(company_id) => {
          onChange({ company_id })
        }}
      />
      <FilterSelect
        label="Found in"
        value={filters.source}
        allLabel="Every source"
        options={entries(SOURCE_LABELS)}
        onChange={(source) => {
          onChange({ source: source as AlternativeSource | undefined })
        }}
      />
      <FilterSelect
        label="Match"
        value={filters.match}
        allLabel="Exact and equivalent"
        options={entries(MATCH_LABELS)}
        onChange={(match) => {
          onChange({ match: match as AlternativeMatch | undefined })
        }}
      />
      <FilterSelect
        label="Kind of item"
        value={filters.item_class}
        allLabel="Materials and goods"
        options={entries(CLASS_LABELS)}
        onChange={(item_class) => {
          onChange({ item_class: item_class as ItemClass | undefined })
        }}
      />
    </div>
  )
}
