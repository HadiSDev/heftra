import {
  Link,
  Outlet,
  createFileRoute,
  useRouterState,
} from '@tanstack/react-router'
import { Tabs, TabsList, TabsTab } from '#/components/ui'
import { usePrincipal } from '#/lib/auth/auth'

export const Route = createFileRoute('/_authed/settings')({
  component: SettingsLayout,
  staticData: { title: 'Settings' },
})

/** The sections, in tab order. */
const TABS = [
  { to: '/settings/profile', label: 'Profile' },
  { to: '/settings/organization', label: 'Organization' },
  { to: '/settings/companies', label: 'Companies' },
  { to: '/settings/spend-trees', label: 'Spend trees' },
] as const

/** Sections only system admins see, after the others. */
const SYSTEM_ADMIN_TABS = [
  { to: '/settings/emission-factors', label: 'Emission factors' },
] as const

function SettingsLayout() {
  const principal = usePrincipal()
  const pathname = useRouterState({
    select: (state) => state.location.pathname,
  })
  const tabs = principal.isSystemAdmin ? [...TABS, ...SYSTEM_ADMIN_TABS] : TABS
  const active =
    tabs.find((tab) => pathname.startsWith(tab.to))?.to ?? TABS[0].to

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-tight">
          Settings
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage your profile, your organization, and the companies it reports
          on.
        </p>
      </div>

      <Tabs value={active}>
        <TabsList>
          {tabs.map((tab) => (
            <TabsTab
              key={tab.to}
              value={tab.to}
              nativeButton={false}
              render={<Link to={tab.to} />}
            >
              {tab.label}
            </TabsTab>
          ))}
        </TabsList>
      </Tabs>

      <Outlet />
    </div>
  )
}
