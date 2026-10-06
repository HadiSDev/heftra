import type { Page } from '@playwright/test'

export interface Persona {
  personName: string
  organizationName: string
}

const hiddenOverlays = [
  '.cl-impersonationFab',
  'button[aria-label="Open TanStack Devtools"]',
  '#tanstack_devtools',
  '[role="region"][aria-label^="Notifications"]',
].join(', ')

export async function hideDevelopmentOverlays(page: Page): Promise<void> {
  await page.addStyleTag({
    content: `${hiddenOverlays} { display: none !important; }`,
  })
}

export async function applyPersona(
  page: Page,
  persona: Persona,
): Promise<void> {
  await page.evaluate(({ personName, organizationName }) => {
    const initialsAvatar = (text: string) => {
      const initials = text
        .split(/\s+/)
        .map((part) => part[0])
        .join('')
        .slice(0, 2)
        .toUpperCase()
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" fill="#3f3f46"/><text x="32" y="41" font-family="Arial, sans-serif" font-size="24" font-weight="600" fill="#ffffff" text-anchor="middle">${initials}</text></svg>`
      return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`
    }

    const replaceText = (root: Element, from: string, to: string) => {
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
      let node = walker.nextNode()
      while (node) {
        if (node.textContent?.includes(from)) {
          node.textContent = node.textContent.split(from).join(to)
        }
        node = walker.nextNode()
      }
    }

    const userAvatar = Array.from(document.querySelectorAll('img')).find(
      (image) =>
        image.alt.trim() !== '' && document.body.innerText.includes(image.alt),
    )
    if (userAvatar) {
      const realName = userAvatar.alt
      replaceText(document.body, realName, personName)
      userAvatar.alt = personName
      userAvatar.src = initialsAvatar(personName)
    }

    const caption = Array.from(document.querySelectorAll('span')).find(
      (span) =>
        span.childElementCount === 0 &&
        span.textContent?.trim() === 'Organization',
    )
    const identity = caption?.parentElement?.parentElement
    if (identity) {
      const organizationLabel = caption?.nextElementSibling
      if (organizationLabel?.textContent) {
        replaceText(
          document.body,
          organizationLabel.textContent,
          organizationName,
        )
      }
      const organizationAvatar = identity.querySelector('img')
      if (organizationAvatar) {
        organizationAvatar.src = initialsAvatar(organizationName)
      }
    }
  }, persona)
}
