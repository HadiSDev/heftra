import { createRouter as createTanStackRouter } from '@tanstack/react-router'
import { setupRouterSsrQueryIntegration } from '@tanstack/react-router-ssr-query'
import { APP_SCROLL_ID } from '#/components/ui'
import { createQueryClient } from '#/lib/query-client'
import { routeTree } from './routeTree.gen'

export function getRouter() {
  const queryClient = createQueryClient()

  const router = createTanStackRouter({
    routeTree,
    scrollRestoration: true,
    scrollToTopSelectors: ['window', `#${APP_SCROLL_ID}`],
    defaultPreload: 'intent',
    defaultPreloadStaleTime: 0,
  })

  setupRouterSsrQueryIntegration({ router, queryClient })

  return router
}

declare module '@tanstack/react-router' {
  interface Register {
    router: ReturnType<typeof getRouter>
  }

  /** Per-route metadata read by the app shell. */
  interface StaticDataRouteOption {
    /** Heading shown in the topbar while this route is matched. */
    title?: string
  }
}
