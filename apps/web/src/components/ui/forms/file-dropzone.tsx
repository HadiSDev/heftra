import * as React from 'react'
import { FileText, UploadCloud, X } from 'lucide-react'
import { cn } from '../cn'

export interface FileDropzoneProps {
  /** The chosen file, or null. */
  value: File | null
  onChange: (file: File | null) => void
  /** Accepted extensions or media types, as for `<input accept>`, e.g. ".xlsx". */
  accept?: string
  /** The largest file accepted, in bytes. */
  maxBytes?: number
  disabled?: boolean
  /** The accessible name of the file input. */
  label: string
  /** The call to action, e.g. "Drop a workbook here". */
  title?: string
  /** What is accepted, e.g. ".xlsx, up to 50 MB". */
  hint?: string
  /** A problem from outside the dropzone, shown below it. */
  error?: string | null
  className?: string
}

const byteUnits = ['B', 'KB', 'MB', 'GB']

/** "12.4 MB" for a byte count. */
export function formatFileSize(bytes: number): string {
  let value = bytes
  let unit = 0
  while (value >= 1024 && unit < byteUnits.length - 1) {
    value /= 1024
    unit += 1
  }
  const digits = unit === 0 || value >= 10 ? 0 : 1
  return `${value.toFixed(digits)} ${byteUnits[unit]}`
}

function acceptsFile(file: File, accept: string | undefined): boolean {
  if (!accept) {
    return true
  }
  const name = file.name.toLowerCase()
  return accept
    .split(',')
    .map((entry) => entry.trim().toLowerCase())
    .filter(Boolean)
    .some((entry) => {
      if (entry.startsWith('.')) {
        return name.endsWith(entry)
      }
      if (entry.endsWith('/*')) {
        return file.type.startsWith(entry.slice(0, -1))
      }
      return file.type === entry
    })
}

/** Why `file` is refused, or null when it is accepted. */
export function fileRejection(
  file: File,
  accept: string | undefined,
  maxBytes: number | undefined,
): string | null {
  if (!acceptsFile(file, accept)) {
    return `${file.name} isn't an accepted file (${accept}).`
  }
  if (maxBytes !== undefined && file.size > maxBytes) {
    return `${file.name} is ${formatFileSize(file.size)}, over the ${formatFileSize(maxBytes)} limit.`
  }
  return null
}

/** Pick one file by dropping it or browsing, with its name and size shown once chosen. */
export function FileDropzone({
  value,
  onChange,
  accept,
  maxBytes,
  disabled = false,
  label,
  title = 'Drop a file here',
  hint,
  error,
  className,
}: FileDropzoneProps) {
  const input = React.useRef<HTMLInputElement>(null)
  const dragDepth = React.useRef(0)
  const [dragging, setDragging] = React.useState(false)
  const [rejection, setRejection] = React.useState<string | null>(null)

  React.useEffect(() => {
    if (value === null && input.current) {
      input.current.value = ''
    }
  }, [value])

  function choose(file: File | undefined) {
    if (!file) {
      return
    }
    const problem = fileRejection(file, accept, maxBytes)
    setRejection(problem)
    onChange(problem ? null : file)
  }

  function browse() {
    if (!disabled) {
      input.current?.click()
    }
  }

  function onDragEnter(event: React.DragEvent) {
    event.preventDefault()
    if (disabled) {
      return
    }
    dragDepth.current += 1
    setDragging(true)
  }

  function onDragLeave(event: React.DragEvent) {
    event.preventDefault()
    dragDepth.current = Math.max(0, dragDepth.current - 1)
    if (dragDepth.current === 0) {
      setDragging(false)
    }
  }

  function onDrop(event: React.DragEvent) {
    event.preventDefault()
    dragDepth.current = 0
    setDragging(false)
    if (!disabled) {
      choose(event.dataTransfer.files[0])
    }
  }

  const message = rejection ?? error ?? null

  return (
    <div className={cn('flex flex-col gap-2', className)}>
      <div
        data-dragging={dragging || undefined}
        data-disabled={disabled || undefined}
        onDragEnter={onDragEnter}
        onDragOver={(event) => {
          event.preventDefault()
        }}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={cn(
          'relative flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed border-border bg-muted/40 px-6 py-8 text-center transition-colors',
          'data-[dragging]:border-primary data-[dragging]:bg-primary/5',
          'data-[disabled]:cursor-not-allowed data-[disabled]:opacity-60',
          message && 'border-destructive/60',
        )}
      >
        <input
          ref={input}
          type="file"
          accept={accept}
          aria-label={label}
          disabled={disabled}
          className="sr-only"
          tabIndex={-1}
          onChange={(event) => {
            choose(event.target.files?.[0])
          }}
        />
        {value ? (
          <div className="flex w-full max-w-md items-center gap-3 rounded-lg border border-border bg-card px-3 py-2.5 text-left shadow-sm">
            <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
              <FileText className="size-5" />
            </span>
            <span className="flex min-w-0 flex-1 flex-col">
              <span className="truncate text-sm font-medium text-foreground">
                {value.name}
              </span>
              <span className="text-xs text-muted-foreground">
                {formatFileSize(value.size)}
              </span>
            </span>
            <button
              type="button"
              aria-label={`Remove ${value.name}`}
              disabled={disabled}
              onClick={() => {
                setRejection(null)
                onChange(null)
              }}
              className="grid size-8 shrink-0 place-items-center rounded-md text-muted-foreground outline-none transition hover:bg-muted hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none"
            >
              <X className="size-4" />
            </button>
          </div>
        ) : (
          <>
            <span className="grid size-12 place-items-center rounded-full bg-primary/10 text-primary">
              <UploadCloud className="size-6" />
            </span>
            <span className="flex flex-col gap-1">
              <span className="text-sm font-medium text-foreground">
                {dragging ? 'Drop to choose it' : title}
              </span>
              {hint ? (
                <span className="text-xs text-muted-foreground">{hint}</span>
              ) : null}
            </span>
          </>
        )}
        <button
          type="button"
          onClick={browse}
          disabled={disabled}
          className="rounded-md px-2 text-sm font-medium text-primary underline-offset-4 outline-none hover:underline focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none"
        >
          {value ? 'Choose another file' : 'Browse files'}
        </button>
      </div>
      {message ? (
        <p role="alert" className="text-sm text-destructive">
          {message}
        </p>
      ) : null}
    </div>
  )
}
