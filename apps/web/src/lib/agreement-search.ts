import type { AgreementRead } from '#/lib/api/agreement-types'

export type AgreementTab = 'terms' | 'report'

/** Which findings the report lists: open ones, reviewed ones, or all. */
export type ReportView = 'open' | 'reviewed' | 'all'

export interface AgreementSearch {
  tab?: AgreementTab
  view?: ReportView
}

const TABS: ReadonlyArray<AgreementTab> = ['terms', 'report']
const VIEWS: ReadonlyArray<ReportView> = ['open', 'reviewed', 'all']

/** The agreement page's tab and findings view from the URL, ignoring anything else. */
export function validateAgreementSearch(
  search: Record<string, unknown>,
): AgreementSearch {
  return {
    tab: TABS.find((tab) => tab === search.tab),
    view: VIEWS.find((view) => view === search.view),
  }
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
