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
