import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

const holdSeconds = 1.8
const rollSeconds = 0.7
const fadeHoldSeconds = 2.4
const fadeSeconds = 0.3

export interface RotatingWordOptions {
  reducedMotion: boolean
}

interface WordSteps {
  viewport: HTMLElement
  track: HTMLElement
  lineHeight: number
  widths: Array<number>
}

function prepareWords(root: HTMLElement): WordSteps | null {
  const viewport = root.querySelector<HTMLElement>('.rotating-word-window')
  const track = root.querySelector<HTMLElement>('[data-rotating-word-track]')
  if (!viewport || !track) {
    return null
  }

  const first = track.firstElementChild
  if (!(first instanceof HTMLElement)) {
    return null
  }
  track.appendChild(first.cloneNode(true))
  root.classList.add('is-rotating')

  const items = Array.from(track.children).filter(
    (item): item is HTMLElement => item instanceof HTMLElement,
  )
  const widths = items.map((item) => item.getBoundingClientRect().width)
  gsap.set(viewport, { width: widths[0] })
  return { viewport, track, lineHeight: first.offsetHeight, widths }
}

function rollTimeline(steps: WordSteps): gsap.core.Timeline {
  const { viewport, track, lineHeight, widths } = steps
  const timeline = gsap.timeline({ repeat: -1, paused: true })
  widths.slice(1).forEach((width, index) => {
    const step = index + 1
    timeline
      .to(
        track,
        { y: -step * lineHeight, duration: rollSeconds, ease: 'expo.inOut' },
        `+=${holdSeconds}`,
      )
      .to(viewport, { width, duration: rollSeconds, ease: 'expo.inOut' }, '<')
  })
  timeline.set(track, { y: 0 })
  return timeline
}

function fadeTimeline(steps: WordSteps): gsap.core.Timeline {
  const { viewport, track, lineHeight, widths } = steps
  const timeline = gsap.timeline({ repeat: -1, paused: true })
  widths.slice(1).forEach((width, index) => {
    const step = index + 1
    timeline
      .to(
        viewport,
        { opacity: 0, duration: fadeSeconds },
        `+=${fadeHoldSeconds}`,
      )
      .set(track, { y: -step * lineHeight })
      .set(viewport, { width })
      .to(viewport, { opacity: 1, duration: fadeSeconds })
  })
  timeline.set(track, { y: 0 })
  return timeline
}

function playWhileVisible(
  root: HTMLElement,
  timeline: gsap.core.Timeline,
): void {
  ScrollTrigger.create({
    trigger: root,
    start: 'top bottom',
    end: 'bottom top',
    onToggle: (self) => {
      if (self.isActive) {
        timeline.play()
      } else {
        timeline.pause()
      }
    },
  })
}

export function initRotatingWords(options: RotatingWordOptions): void {
  document
    .querySelectorAll<HTMLElement>('[data-rotating-word]')
    .forEach((root) => {
      const steps = prepareWords(root)
      if (!steps) {
        return
      }
      const timeline = options.reducedMotion
        ? fadeTimeline(steps)
        : rollTimeline(steps)
      playWhileVisible(root, timeline)
    })
}
