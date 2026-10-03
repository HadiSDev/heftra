import type { AgreementRead, FindingSort } from '#/lib/api/agreement-types'
import type { SortOrder } from '#/lib/api/types'
import { oneOf, sortOrder } from '#/lib/sorting'
import type { SortState } from '#/lib/sorting'

export type AgreementTab = 'terms' | 'report'

/** Which findings the report lists: open ones, reviewed ones, or all. */
export type ReportView = 'open' | 'reviewed' | 'all'

export interface AgreementSearch {
  tab?: AgreementTab
  view?: ReportView
  sort?: FindingSort
  order?: SortOrder
}

const TABS: ReadonlyArray<AgreementTab> = ['terms', 'report']
const VIEWS: ReadonlyArray<ReportView> = ['open', 'reviewed', 'all']
const FINDING_SORTS: ReadonlyArray<FindingSort> = [
  'severity',
  'amount',
  'spent_on',
  'supplier',
  'item',
]

/** The agreement page's tab, findings view and sort from the URL, ignoring anything else. */
export function validateAgreementSearch(
  search: Record<string, unknown>,
): AgreementSearch {
  return {
    tab: TABS.find((tab) => tab === search.tab),
    view: VIEWS.find((view) => view === search.view),
    sort: oneOf(search.sort, FINDING_SORTS),
    order: sortOrder(search.order),
  }
}

/** The order a findings sort starts in: supplier and item A–Z, the rest largest, newest or
 * most severe first. */
export function defaultFindingOrder(sort: FindingSort): SortOrder {
  return sort === 'supplier' || sort === 'item' ? 'asc' : 'desc'
}

/** The findings sort in effect: the URL's, else rule breaks first. */
export function resolveFindingSort(
  search: AgreementSearch,
): SortState<FindingSort> {
  const sort = search.sort ?? 'severity'
  return { sort, order: search.order ?? defaultFindingOrder(sort) }
}

/** The tab an agreement opens on: its report once it is active and nothing is left to review. */
export function defaultAgreementTab(
  agreement: Pick<AgreementRead, 'status' | 'terms'> | undefined,
): AgreementTab {
  if (agreement?.status !== 'active') {
    return 'terms'
  }
  const drafts = agreement.terms.some((term) => term.status === 'draft')
  return drafts ? 'terms' : 'report'
}
