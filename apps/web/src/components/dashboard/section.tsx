import { Card, Skeleton, cn } from '#/components/ui'

export interface DashboardSectionProps {
  title: string
  /** A line under the title, such as the comparison period. */
  description?: React.ReactNode
  loading: boolean
  error: boolean
  /** The section's height while it loads, matching its content so nothing shifts. */
  placeholderClassName: string
  className?: string
  children: React.ReactNode
}

/** One card of the dashboard, holding its place while it loads and failing on its own. */
export function DashboardSection({
  title,
  description,
  loading,
  error,
  placeholderClassName,
  className,
  children,
}: DashboardSectionProps) {
  return (
    <Card className={cn('flex min-w-0 flex-col', className)}>
      <section aria-label={title} className="flex min-w-0 flex-col gap-4 p-5">
        <header className="flex flex-col gap-0.5">
          <h2 className="font-display text-base font-medium tracking-tight">
            {title}
          </h2>
          {description ? (
            <p className="text-xs text-muted-foreground">{description}</p>
          ) : null}
        </header>
        {error ? (
          <p
            role="alert"
            className={cn(
              'grid place-items-center text-center text-sm text-muted-foreground',
              placeholderClassName,
            )}
          >
            Couldn’t load this part of the dashboard. Reload to try again.
          </p>
        ) : loading ? (
          <Skeleton
            data-testid={`${title}-loading`}
            className={cn('w-full rounded-lg', placeholderClassName)}
          />
        ) : (
          children
        )}
      </section>
    </Card>
  )
}
