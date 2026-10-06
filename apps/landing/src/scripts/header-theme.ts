function headerStripMargin(nav: HTMLElement): string {
  const bottom = nav.getBoundingClientRect().bottom
  const viewport = window.innerHeight
  return `0px 0px -${Math.max(viewport - bottom, 0)}px 0px`
}

export function initHeaderTheme(): void {
  const nav = document.querySelector<HTMLElement>('[data-header-nav]')
  const darkSections = document.querySelectorAll<HTMLElement>('section.dark')
  if (!nav || darkSections.length === 0) {
    return
  }

  const underHeader = new Set<Element>()
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          underHeader.add(entry.target)
        } else {
          underHeader.delete(entry.target)
        }
      })
      nav.classList.toggle('dark', underHeader.size > 0)
    },
    { rootMargin: headerStripMargin(nav), threshold: 0 },
  )
  darkSections.forEach((section) => {
    observer.observe(section)
  })
}
