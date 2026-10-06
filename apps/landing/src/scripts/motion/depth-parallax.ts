import { gsap } from 'gsap'
import type { MotionContext } from './index'

const depthFactors: Record<string, number> = {
  '0': 0.1,
  '1': 0.25,
  '2': 0.5,
  '3': 0.8,
  '4': 1,
  '5': 1.2,
}

function parallaxLayers(scene: HTMLElement, distance: number): void {
  scene
    .querySelectorAll<HTMLElement>(':scope > .layer[data-depth]')
    .forEach((layer) => {
      const factor = depthFactors[layer.dataset.depth ?? '4'] ?? 1
      const shift = (1 - factor) * distance
      if (shift === 0) {
        return
      }
      gsap.to(layer, {
        y: shift,
        ease: 'none',
        scrollTrigger: {
          trigger: scene,
          start: 'top top',
          end: 'bottom top',
          scrub: true,
        },
      })
    })
}

function heroProductTilt(hero: HTMLElement): void {
  const product = hero.querySelector<HTMLElement>('[data-hero-product]')
  if (!product) {
    return
  }
  gsap.fromTo(
    product,
    { rotateX: 14, transformOrigin: '50% 0%' },
    {
      rotateX: 0,
      ease: 'none',
      scrollTrigger: {
        trigger: product,
        start: 'top 95%',
        end: 'top 25%',
        scrub: true,
      },
    },
  )
}

function heroChipScatter(hero: HTMLElement, distance: number): void {
  hero.querySelectorAll<HTMLElement>('[data-chip]').forEach((chip) => {
    const direction = chip.dataset.chip === 'left' ? -1 : 1
    gsap.to(chip, {
      x: direction * distance * 0.6,
      y: -distance * 0.4,
      rotate: direction * 6,
      opacity: 0,
      ease: 'none',
      scrollTrigger: {
        trigger: hero,
        start: 'center top+=35%',
        end: 'bottom top',
        scrub: true,
      },
    })
  })
}

export function initDepthParallax(context: MotionContext): void {
  const distance = context.coarsePointer ? 80 : 180
  document.querySelectorAll<HTMLElement>('[data-scene]').forEach((scene) => {
    parallaxLayers(scene, distance)
  })

  const hero = document.querySelector<HTMLElement>('[data-scene="hero"]')
  if (!hero) {
    return
  }
  heroProductTilt(hero)
  heroChipScatter(hero, distance)
}
