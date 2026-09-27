import * as React from 'react'
import {
  Link,
  useMatches,
  useNavigate,
  useRouterState,
} from '@tanstack/react-router'
import { useClerk, useUser } from '@clerk/tanstack-react-start'

import { Logo } from '#/components/brand/logo'
import {
  Building2,
  ChevronDown,
  LayoutDashboard,
  Leaf,
  LogOut,
  Moon,
  Receipt,
  Settings,
  Sun,
} from 'lucide-react'
import {
  AppShell,
  Avatar,
  AvatarFallback,
  AvatarImage,
  Badge,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  IconButton,
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarNav,
  SidebarNavItem,
  Topbar,
  TopbarActions,
  TopbarTitle,
  sidebarNavItemClass,
  useTheme,
} from '#/components/ui'
import { OrgSwitcher } from '#/components/org-switcher'
import { usePrincipal } from '#/lib/auth/auth'
import { initials } from '#/lib/format/initials'

const ROLE_LABELS: Record<string, string> = {
  admin: 'Admin',
  moderator: 'Moderator',
  member: 'Member',
  viewer: 'Viewer',
}

function UserMenu() {
  const principal = usePrincipal()
  const { user } = useUser()
  const { signOut } = useClerk()
  const navigate = useNavigate()

  const name = user?.fullName || user?.username || principal.name
  const email = user?.primaryEmailAddress?.emailAddress || principal.email
  const imageUrl = user?.hasImage ? user.imageUrl : undefined
  const roleLabel = principal.isSystemAdmin
    ? 'System admin'
    : (ROLE_LABELS[principal.role] ?? principal.role)

  async function handleSignOut() {
    await signOut()
    await navigate({ to: '/sign-in' })
  }

  const avatar = (className?: string) => (
    <Avatar className={className}>
      {imageUrl ? <AvatarImage src={imageUrl} alt={name} /> : null}
      <AvatarFallback>{initials(name)}</AvatarFallback>
    </Avatar>
  )

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <button
            type="button"
            className="flex items-center gap-2 rounded-full py-1 pr-2 pl-1 outline-none transition-colors hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring"
          >
            {avatar('size-8')}
            <span className="hidden max-w-36 truncate text-sm font-medium sm:block">
              {name}
            </span>
            <ChevronDown className="hidden size-4 text-muted-foreground sm:block" />
          </button>
        }
      />
      <DropdownMenuContent align="end" className="w-64">
        <div className="flex items-center gap-3 px-2 py-2">
          {avatar('size-10')}
          <div className="min-w-0">
            <div className="truncate text-sm font-medium text-foreground">
              {name}
            </div>
            <div className="truncate text-xs text-muted-foreground">
              {email}
            </div>
          </div>
        </div>
        <div className="px-2 pb-2">
          <Badge variant={principal.isSystemAdmin ? 'info' : 'outline'}>
            {roleLabel}
          </Badge>
        </div>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          render={
            <Link to="/settings">
              <Settings />
              Settings
            </Link>
          }
        />
        <DropdownMenuItem onClick={handleSignOut}>
          <LogOut />
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

/** Sidebar navigation. Entries without a `to` are pages that don't exist yet. */
export const NAV_ITEMS = [
  { label: 'Dashboard', icon: LayoutDashboard, to: '/' },
  { label: 'Spend Lines', icon: Receipt, to: '/invoice-lines' },
  { label: 'Suppliers', icon: Building2, to: '/suppliers' },
  { label: 'Settings', icon: Settings, to: '/settings' },
] as const

/** System-admin pages, listed at the bottom of the sidebar for system admins only. */
export const ADMIN_NAV_ITEMS = [
  { label: 'Emission factors', icon: Leaf, to: '/admin/emission-factors' },
] as const

/** Whether a nav entry matches the current location. */
export function isNavItemActive(pathname: string, to: string): boolean {
  if (to === '/') {
    return pathname === '/'
  }
  return pathname === to || pathname.startsWith(`${to}/`)
}

/** The system-admin entries under a "System" caption. */
function AdminNav({ pathname }: { pathname: string }) {
  return (
    <SidebarFooter className="border-t border-border pt-3">
      <p className="px-3 pb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
        System
      </p>
      <SidebarNav aria-label="System">
        {ADMIN_NAV_ITEMS.map(({ label, icon: Icon, to }) => {
          const active = isNavItemActive(pathname, to)
          return (
            <Link
              key={label}
              to={to}
              className={sidebarNavItemClass(active)}
              aria-current={active ? 'page' : undefined}
            >
              <Icon />
              <span className="truncate">{label}</span>
            </Link>
          )
        })}
      </SidebarNav>
    </SidebarFooter>
  )
}

/** The sidebar, driven by the current pathname. Presentational. */
export function AppSidebar({
  pathname,
  isSystemAdmin = false,
}: {
  pathname: string
  isSystemAdmin?: boolean
}) {
  return (
    <Sidebar>
      <SidebarHeader className="flex-col items-stretch gap-2">
        <Logo width={124} className="my-1" />
        <OrgSwitcher />
      </SidebarHeader>
      <SidebarContent>
        <SidebarNav>
          {NAV_ITEMS.map(({ label, icon: Icon, ...item }) => {
            const to = 'to' in item ? item.to : undefined
            if (!to) {
              return (
                <SidebarNavItem key={label} icon={<Icon />} disabled>
                  {label}
                </SidebarNavItem>
              )
            }
            const active = isNavItemActive(pathname, to)
            return (
              <Link
                key={label}
                to={to}
                className={sidebarNavItemClass(active)}
                aria-current={active ? 'page' : undefined}
              >
                <Icon />
                <span className="truncate">{label}</span>
              </Link>
            )
          })}
        </SidebarNav>
      </SidebarContent>
      {isSystemAdmin ? <AdminNav pathname={pathname} /> : null}
    </Sidebar>
  )
}

/** The topbar title, declared per route via `staticData.title`. */
function usePageTitle(): string {
  const matches = useMatches()
  for (let i = matches.length - 1; i >= 0; i--) {
    const title = matches[i].staticData.title
    if (title) {
      return title
    }
  }
  return 'Dashboard'
}

/** The application shell for every authenticated route. */
export function AppLayout({ children }: { children: React.ReactNode }) {
  const { theme, toggleTheme } = useTheme()
  const principal = usePrincipal()
  const pathname = useRouterState({
    select: (state) => state.location.pathname,
  })
  const title = usePageTitle()

  return (
    <AppShell
      sidebar={
        <AppSidebar
          pathname={pathname}
          isSystemAdmin={principal.isSystemAdmin}
        />
      }
      header={
        <Topbar>
          <TopbarTitle>{title}</TopbarTitle>
          <TopbarActions>
            <IconButton
              aria-label="Toggle theme"
              variant="outline"
              onClick={toggleTheme}
            >
              {theme === 'dark' ? <Sun /> : <Moon />}
            </IconButton>
            <UserMenu key={principal.id} />
          </TopbarActions>
        </Topbar>
      }
    >
      {children}
    </AppShell>
  )
}
