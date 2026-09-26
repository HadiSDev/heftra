import { Card } from '#/components/ui'

/** One dashboard tile: an icon, a caption and its figures. */
export function Tile({
  caption,
  icon,
  children,
}: {
  caption: string
  icon: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <Card className="flex min-w-0 flex-col gap-3 p-5">
      <section aria-label={caption} className="flex min-w-0 flex-col gap-3">
        <header className="flex items-center gap-2">
          <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-primary text-primary-foreground [&_svg]:size-4">
            {icon}
          </span>
          <h2 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
            {caption}
          </h2>
        </header>
        {children}
      </section>
    </Card>
  )
}

/** A currency's figure when more than one currency is shown. */
export function CurrencyCaption({
  currency,
  shown,
}: {
  currency: string
  shown: boolean
}) {
  if (!shown) {
    return null
  }
  return (
    <span className="text-xs font-medium text-muted-foreground">
      {currency}
    </span>
  )
}
