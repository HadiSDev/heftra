import type { Money, Page } from './types'

export type ItemClass = 'material' | 'part' | 'finished_good'
export type PricingUnit =
  'kg' | 'm' | 'm2' | 'm3' | 'l' | 'piece' | 'sheet' | 'roll' | 'pack'
export type AlternativeSource = 'history' | 'benchmark' | 'marketplace'
export type AlternativeMatch = 'exact' | 'equivalent'
export type AlternativeReviewStatus = 'open' | 'dismissed' | 'switched'
export type DismissReason =
  'not_equivalent' | 'supplier_not_approved' | 'price_wrong' | 'other'
export type AttributeKind = 'numeric' | 'tiered' | 'other'
export type Direction = 'more' | 'less' | 'equal'
export type Verdict = 'same' | 'better' | 'worse' | 'missing'
/** Why an item has no unit price. */
export type PriceNote =
  'not_bought' | 'no_specification' | 'no_pack_size' | 'no_quantity'

export interface Attribute {
  name: string
  kind: AttributeKind
  value: string
  number: number | null
  unit: string | null
  direction: Direction
  family: string | null
  tier: string | null
  generation: string | null
}

/** What an item is, what a buyer must not get less of, and how it is priced. */
export interface Specification {
  item_class: ItemClass
  product_type: string
  name: string
  brand: string | null
  model: string | null
  part_number: string | null
  gtin: string | null
  attributes: Array<Attribute>
  pricing_unit: PricingUnit
  units_per_line_unit: number | null
  confidence: number
}

export interface AttributeComparison {
  name: string
  item: string
  candidate: string | null
  verdict: Verdict
  reason: string
}

export interface AgreementNote {
  kind: 'off_contract' | 'commitment_behind'
  agreement_id: string
  term_id: string
  text: string
}

/** Where an alternative came from; which keys are set depends on its source. */
export interface AlternativeOrigin {
  supplier?: string | null
  company?: string | null
  last_bought_on?: string | null
  organizations?: number
  median?: string
  lowest_quartile?: string
  by?: 'product' | 'specification'
  connector?: string
  seller?: string
  url?: string
  seen_at?: string
  availability?: string | null
  shipping?: string | null
}

export interface AlternativeRead {
  id: string
  item_id: string
  source: AlternativeSource
  match: AlternativeMatch
  name: string
  /** Per the item's pricing unit, without VAT, in `currency`. */
  unit_price: Money
  currency: string
  saving_yearly: Money | null
  saving_percent: Money
  comparison: Array<AttributeComparison>
  origin: AlternativeOrigin
  agreement_notes: Array<AgreementNote>
  review_status: AlternativeReviewStatus
  dismiss_reason: DismissReason | null
  review_note: string | null
  reviewed_by_name: string | null
  reviewed_at: string | null
  found_at: string
}

export interface ItemSummary {
  id: string
  company_id: string
  name: string
  supplier_name: string | null
  item_class: ItemClass | null
  pricing_unit: PricingUnit | null
  unit_price: Money | null
  quantity: Money | null
  currency: string | null
  alternatives: number
  best: AlternativeRead | null
}

export interface AlternativesPage extends Page<ItemSummary> {
  /** The listed items' best yearly savings added up, when they share a currency. */
  total_saving: Money | null
  currency: string | null
  /** How many of the companies' items have been searched. */
  searched_items: number
}

export interface ItemRead {
  id: string
  company_id: string
  item_name: string | null
  description: string | null
  unit: string | null
  vendor_id: string | null
  supplier_name: string | null
  category_path: Array<string>
  spec: Specification | null
  spec_source: 'ai' | 'human' | null
  spend: Money
  lines: number
  last_bought_on: string | null
  quantity: Money | null
  unit_price: Money | null
  currency: string | null
  price_note: PriceNote | null
  searched_at: string | null
  searching: boolean
  alternatives: Array<AlternativeRead>
}

export interface AlternativeReview {
  review_status: AlternativeReviewStatus
  dismiss_reason?: DismissReason | null
  note?: string | null
}

export interface AlternativeFilters {
  company_id?: string
  source?: AlternativeSource
  match?: AlternativeMatch
  item_class?: ItemClass
  page?: number
}
