import { toastManager } from '#/components/ui'
import { isDemoRefusal } from '#/lib/api/demo-refusal'

/** The toast shown whenever the demo declines to save a change. */
export const DEMO_NOTICE = {
  title: 'Changes aren’t saved in the demo',
  description: 'Try anything you like — the demo resets every night.',
} as const

/** Tells the visitor their change wasn't saved. */
export function announceDemoRefusal(): void {
  toastManager.add(DEMO_NOTICE)
}

/** Announces `error` when it is the demo's refusal; a mutation cache's `onError`. */
export function announceIfDemoRefusal(error: unknown): void {
  if (isDemoRefusal(error)) {
    announceDemoRefusal()
  }
}
