function setOpen(
  button: HTMLButtonElement,
  panel: HTMLElement,
  open: boolean,
): void {
  button.setAttribute('aria-expanded', String(open))
  button.setAttribute('aria-label', open ? 'Close menu' : 'Open menu')
  button.querySelector('.menu-open-icon')?.classList.toggle('hidden', open)
  button.querySelector('.menu-close-icon')?.classList.toggle('hidden', !open)
  panel.hidden = !open
}

function initMenu(root: HTMLElement): void {
  const button = root.querySelector<HTMLButtonElement>(
    '[data-mobile-menu-button]',
  )
  const panel = root.querySelector<HTMLElement>('[data-mobile-menu-panel]')
  if (!button || !panel) {
    return
  }

  const close = (returnFocus: boolean) => {
    setOpen(button, panel, false)
    if (returnFocus) {
      button.focus()
    }
  }

  button.addEventListener('click', () => {
    const open = button.getAttribute('aria-expanded') !== 'true'
    setOpen(button, panel, open)
    if (open) {
      panel.querySelector<HTMLElement>('a')?.focus()
    }
  })

  panel.addEventListener('click', (event) => {
    if (event.target instanceof HTMLElement && event.target.closest('a')) {
      close(false)
    }
  })

  document.addEventListener('keydown', (event) => {
    if (
      event.key === 'Escape' &&
      button.getAttribute('aria-expanded') === 'true'
    ) {
      close(true)
    }
  })

  document.addEventListener('click', (event) => {
    if (event.target instanceof Node && !root.contains(event.target)) {
      setOpen(button, panel, false)
    }
  })
}

export function initMobileMenus(): void {
  document.querySelectorAll<HTMLElement>('[data-mobile-menu]').forEach(initMenu)
}
