import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { releaseWillChange } from './gpu'

const heroSelector = '[data-scene="hero"]'

const lineHidden = { yPercent: 105, y: 0 }
const lineShown = { yPercent: 0, y: 0 }
const fadeHidden = { opacity: 0, y: 16 }
const fadeShown = { opacity: 1, y: 0 }

function lineSpans(element: Element): Array<HTMLElement> {
  return Array.from(
    element.querySelectorAll<HTMLElement>('.reveal-line > span'),
  )
}

export function initHeroEntrance(): void {
  const hero = document.querySelector<HTMLElement>(heroSelector)
  if (!hero) {
    return
  }
  const headline = hero.querySelector('[data-reveal="lines"]')
  const fades = hero.querySelectorAll<HTMLElement>('[data-reveal="fade"]')
  const product = hero.querySelector<HTMLElement>('[data-hero-product]')
  const chips = hero.querySelectorAll<HTMLElement>('[data-chip]')

  const timeline = gsap.timeline({ defaults: { ease: 'expo.out' } })
  if (headline) {
    timeline.fromTo(lineSpans(headline), lineHidden, {
      ...lineShown,
      duration: 1.2,
      stagger: 0.12,
      willChange: 'transform',
      onComplete: releaseWillChange,
    })
  }
  timeline.fromTo(
    fades,
    { opacity: 0, y: 18 },
    { ...fadeShown, duration: 0.9, stagger: 0.08 },
    '-=0.8',
  )
  if (product) {
    timeline.fromTo(
      product,
      { opacity: 0, y: 80, scale: 0.94 },
      { opacity: 1, y: 0, scale: 1, duration: 1.4, ease: 'power3.out' },
      '-=0.9',
    )
  }
  timeline.fromTo(
    chips,
    { opacity: 0, scale: 0.85, y: 24 },
    {
      opacity: 1,
      scale: 1,
      y: 0,
      duration: 0.9,
      stagger: 0.12,
      ease: 'back.out(1.6)',
    },
    '-=0.6',
  )
}

export function initTextReveals(): void {
  document
    .querySelectorAll<HTMLElement>('[data-reveal="lines"]')
    .forEach((element) => {
      if (element.closest(heroSelector)) {
        return
      }
      gsap.fromTo(lineSpans(element), lineHidden, {
        ...lineShown,
        duration: 1.1,
        stagger: 0.1,
        ease: 'expo.out',
        scrollTrigger: { trigger: element, start: 'top 85%', once: true },
      })
    })

  document
    .querySelectorAll<HTMLElement>('[data-reveal="fade"]')
    .forEach((element) => {
      if (element.closest(heroSelector)) {
        return
      }
      gsap.fromTo(element, fadeHidden, {
        ...fadeShown,
        duration: 0.9,
        ease: 'power2.out',
        scrollTrigger: { trigger: element, start: 'top 88%', once: true },
      })
    })
}

export function initWordLighting(): void {
  document
    .querySelectorAll<HTMLElement>('[data-word-light]')
    .forEach((paragraph) => {
      const words = Array.from(paragraph.querySelectorAll<HTMLElement>('.word'))
      ScrollTrigger.create({
        trigger: paragraph,
        start: 'top 80%',
        end: 'bottom 45%',
        scrub: true,
        onUpdate: (self) => {
          const lit = Math.round(self.progress * words.length)
          words.forEach((word, index) => {
            word.classList.toggle('is-lit', index < lit)
          })
        },
      })
    })
}
