import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { initCounters } from './counters'
import { initDepthParallax } from './depth-parallax'
import { initPinnedSteps } from './pinned-steps'
import { initRotatingWords } from './rotating-words'
import { initStaggerGrid } from './stagger-grid'
import {
  initHeroEntrance,
  initTextReveals,
  initWordLighting,
} from './text-reveals'

export interface MotionContext {
  coarsePointer: boolean
}

function finishMotionSetup(root: HTMLElement): void {
  root.classList.add('motion-ready')
  root.classList.remove('motion-pending')
}

export function initMotion(): void {
  const root = document.documentElement
  gsap.registerPlugin(ScrollTrigger)
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    root.classList.remove('motion-pending')
    initRotatingWords({ reducedMotion: true })
    return
  }

  const context: MotionContext = {
    coarsePointer: window.matchMedia('(pointer: coarse)').matches,
  }

  initPinnedSteps(context)
  initDepthParallax(context)
  initHeroEntrance()
  initTextReveals()
  initWordLighting()
  initStaggerGrid()
  initCounters()
  initRotatingWords({ reducedMotion: false })
  ScrollTrigger.sort()

  finishMotionSetup(root)
  window.addEventListener('load', () => {
    ScrollTrigger.refresh()
  })
}
