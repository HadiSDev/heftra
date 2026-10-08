import { MutationCache, QueryClient } from '@tanstack/react-query'
import { announceIfDemoRefusal } from '#/lib/demo/demo-notice'

/** The app's query client; every failed mutation the demo refused is announced once, here. */
export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
    mutationCache: new MutationCache({ onError: announceIfDemoRefusal }),
  })
}
