type Theme = 'light' | 'dark'

const storageKey = 'steelyard-theme'

function currentTheme(): Theme {
  return document.documentElement.classList.contains('dark') ? 'dark' : 'light'
}

function storeTheme(theme: Theme): void {
  try {
    window.localStorage.setItem(storageKey, theme)
  } catch {
    return
  }
}

function labelFor(theme: Theme): string {
  return theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'
}

function applyTheme(
  theme: Theme,
  toggles: NodeListOf<HTMLButtonElement>,
): void {
  document.documentElement.classList.toggle('dark', theme === 'dark')
  toggles.forEach((toggle) => {
    toggle.setAttribute('aria-label', labelFor(theme))
  })
}

export function initThemeToggles(): void {
  const toggles = document.querySelectorAll<HTMLButtonElement>(
    '[data-theme-toggle]',
  )
  applyTheme(currentTheme(), toggles)
  toggles.forEach((toggle) => {
    toggle.addEventListener('click', () => {
      const next: Theme = currentTheme() === 'dark' ? 'light' : 'dark'
      applyTheme(next, toggles)
      storeTheme(next)
    })
  })
}
