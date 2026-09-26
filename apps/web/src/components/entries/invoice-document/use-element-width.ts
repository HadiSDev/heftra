import * as React from 'react'

/** The content width of the element the returned ref is attached to, kept up to date as it resizes. */
export function useElementWidth<T extends HTMLElement>(): [
  React.RefCallback<T>,
  number | undefined,
] {
  const [element, setElement] = React.useState<T | null>(null)
  const [width, setWidth] = React.useState<number | undefined>(undefined)

  React.useEffect(() => {
    if (!element) {
      return
    }
    setWidth(element.clientWidth || undefined)
    if (typeof ResizeObserver === 'undefined') {
      return
    }
    const observer = new ResizeObserver((entries) => {
      const next = Math.floor(entries[0].contentRect.width)
      setWidth(next || undefined)
    })
    observer.observe(element)
    return () => observer.disconnect()
  }, [element])

  return [setElement, width]
}
