import type { Money } from './types'

/** The period a spend report covers, as ISO dates. */
export interface PeriodRead {
  start: string
  end: string
}

/** The period asked for and the one the report compared it with. */
export interface ReportPeriods {
  period: PeriodRead
  comparison: PeriodRead
}

/** One month's spend. */
export interface MonthSpend {
  month: string
  amount: Money
}

/** One base currency's tiles. */
export interface SpendOverviewRow {
  currency: string
  spend: Money
  comparison_spend: Money
  categorized_spend: Money
  unconverted_vouchers: number
  months: Array<MonthSpend>
  active_suppliers: number
  new_suppliers: number
}

/** Work waiting across the companies, whatever the period. */
export interface AttentionCounts {
  needs_review_lines: number
  failed_documents: number
  totals_mismatch: number
}

/** `GET /reports/spend-overview`. */
export interface SpendOverview extends ReportPeriods {
  rows: Array<SpendOverviewRow>
  attention: AttentionCounts
}

/** One stack of the trend: a named category, the rest together, or the uncategorized spend. */
export interface TrendSeries {
  kind: 'category' | 'other' | 'not_categorized'
  name: string | null
  amounts: Array<Money>
}

export interface SpendTrendRow {
  currency: string
  months: Array<string>
  series: Array<TrendSeries>
}

/** `GET /reports/spend-trend`. */
export interface SpendTrend extends ReportPeriods {
  rows: Array<SpendTrendRow>
}

/** A category's spend in both periods; `name` is null for the uncategorized spend. */
export interface CategorySpendRead {
  name: string | null
  spend: Money
  comparison_spend: Money
  children: Array<CategorySpendRead>
}

export interface SupplierSpendRead {
  id: string
  name: string
  country_code: string | null
  spend: Money
  comparison_spend: Money
}

export interface SpendBreakdownRow {
  currency: string
  spend: Money
  categories: Array<CategorySpendRead>
  suppliers: Array<SupplierSpendRead>
}

/** `GET /reports/spend-breakdown`. */
export interface SpendBreakdown extends ReportPeriods {
  rows: Array<SpendBreakdownRow>
}

/** A supplier and the amount an insight is about: its spend, its rise, or its monthly average. */
export interface SupplierInsight {
  id: string
  name: string
  amount: Money
  comparison_amount: Money | null
  active_months: number | null
}

/** A voucher whose spend is not categorized, addressed as Spend Lines opens it. */
export interface UncategorizedInsight {
  voucher_id: string | null
  entry_id: string | null
  invoice_id: string | null
  supplier_id: string | null
  supplier_name: string | null
  spent_on: string
  amount: Money
}

export interface SpendInsightsRow {
  currency: string
  new_suppliers: Array<SupplierInsight>
  increases: Array<SupplierInsight>
  recurring: Array<SupplierInsight>
  uncategorized: Array<UncategorizedInsight>
}

/** `GET /reports/spend-insights`. */
export interface SpendInsights extends ReportPeriods {
  rows: Array<SpendInsightsRow>
}

/** Which spend a report is for: a period and, optionally, one company. */
export interface SpendScope {
  from: string
  to: string
  company_id?: string
}
