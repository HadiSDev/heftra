import { gsap } from 'gsap'

const formatter = new Intl.NumberFormat('en-IE')

export function initCounters(): void {
  document
    .querySelectorAll<HTMLElement>('[data-count-to]')
    .forEach((element) => {
      const target = Number(element.dataset.countTo)
      if (!Number.isFinite(target)) {
        return
      }
      const counter = { value: 0 }
      element.textContent = formatter.format(0)
      gsap.to(counter, {
        value: target,
        duration: 1.6,
        ease: 'power2.out',
        scrollTrigger: { trigger: element, start: 'top 90%', once: true },
        onUpdate: () => {
          element.textContent = formatter.format(Math.round(counter.value))
        },
      })
    })
}
