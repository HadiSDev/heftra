import { gsap } from 'gsap'
import { releaseWillChange } from './gpu'

const hidden = { opacity: 0, y: 40 }

function riseOnEnter(trigger: Element, targets: Array<HTMLElement>): void {
  gsap.set(targets, { ...hidden, willChange: 'transform, opacity' })
  gsap.to(targets, {
    opacity: 1,
    y: 0,
    duration: 0.9,
    stagger: 0.09,
    ease: 'power3.out',
    onComplete: releaseWillChange,
    scrollTrigger: { trigger, start: 'top 90%', once: true },
  })
}

export function initStaggerGrid(): void {
  gsap.utils.toArray<HTMLElement>('[data-stagger]').forEach((group) => {
    const items = Array.from(
      group.querySelectorAll<HTMLElement>(':scope > [data-reveal="rise"]'),
    )
    if (items.length > 0) {
      riseOnEnter(group, items)
    }
  })

  gsap.utils
    .toArray<HTMLElement>('[data-reveal="rise"]')
    .filter((element) => !element.parentElement?.hasAttribute('data-stagger'))
    .forEach((element) => {
      riseOnEnter(element, [element])
    })

  gsap.utils.toArray<HTMLElement>('[data-reveal="iris"]').forEach((element) => {
    gsap.fromTo(
      element,
      {
        clipPath: 'inset(14% 10% 14% 10% round 28px)',
        opacity: 0.4,
        scale: 0.96,
      },
      {
        clipPath: 'inset(0% 0% 0% 0% round 20px)',
        opacity: 1,
        scale: 1,
        ease: 'power2.out',
        scrollTrigger: {
          trigger: element,
          start: 'top 90%',
          end: 'top 45%',
          scrub: 0.6,
        },
      },
    )
  })
}
