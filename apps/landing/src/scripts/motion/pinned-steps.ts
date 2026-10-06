import { gsap } from 'gsap'
import type { MotionContext } from './index'

const pinnedQuery = '(min-width: 1024px) and (min-height: 720px)'

function buildPinnedScene(track: HTMLElement): () => void {
  const steps = Array.from(
    track.querySelectorAll<HTMLElement>('[data-how-step]'),
  )
  const copies = steps.map((step) =>
    step.querySelector<HTMLElement>('.how-copy'),
  )
  const visuals = steps.map((step) =>
    step.querySelector<HTMLElement>('.how-visual'),
  )
  const bars = steps.map((step) =>
    step.querySelector<HTMLElement>('.how-progress-bar'),
  )

  track.classList.add('is-pinned')
  gsap.set(copies, { opacity: 0.32 })
  gsap.set(copies[0], { opacity: 1 })
  gsap.set(visuals.slice(1), { clipPath: 'inset(100% 0% 0% 0% round 20px)' })
  gsap.set(visuals[0], { clipPath: 'inset(0% 0% 0% 0% round 20px)' })

  const timeline = gsap.timeline({
    defaults: { ease: 'none' },
    scrollTrigger: {
      trigger: track,
      start: 'center center',
      end: () => `+=${window.innerHeight * steps.length * 0.9}`,
      pin: true,
      scrub: 0.5,
      anticipatePin: 1,
      invalidateOnRefresh: true,
    },
  })

  steps.forEach((_, index) => {
    timeline.to(bars[index], { scaleX: 1, duration: 1 })
    const next = index + 1
    if (next >= steps.length) {
      return
    }
    timeline
      .to(copies[index], { opacity: 0.32, duration: 0.25 })
      .to(copies[next], { opacity: 1, duration: 0.25 }, '<')
      .to(
        visuals[next],
        {
          clipPath: 'inset(0% 0% 0% 0% round 20px)',
          duration: 0.5,
          ease: 'power2.inOut',
        },
        '<',
      )
      .to(visuals[index], { scale: 0.94, opacity: 0.5, duration: 0.5 }, '<')
  })

  return () => {
    track.classList.remove('is-pinned')
    gsap.set([...copies, ...visuals, ...bars], { clearProps: 'all' })
  }
}

export function initPinnedSteps(context: MotionContext): void {
  const track = document.querySelector<HTMLElement>('[data-how-track]')
  if (!track || context.coarsePointer) {
    return
  }
  const media = gsap.matchMedia()
  media.add(pinnedQuery, () => buildPinnedScene(track))
}
