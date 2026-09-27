import * as React from 'react'
import { Upload } from 'lucide-react'
import {
  Button,
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
  Checkbox,
  Progress,
} from '#/components/ui'

/** The largest workbook the API accepts. */
export const MAX_WORKBOOK_BYTES = 50 * 1024 * 1024

export interface WorkbookUploadProps {
  /** A workbook import is queued or running, so another can't start. */
  importing: boolean
  onUpload: (
    file: File,
    activate: boolean,
    onProgress: (sent: number) => void,
  ) => Promise<void>
}

/** Why `file` can't be uploaded, or null when it can. */
export function workbookProblem(file: File): string | null {
  if (!file.name.toLowerCase().endsWith('.xlsx')) {
    return `${file.name} is not an .xlsx workbook.`
  }
  if (file.size > MAX_WORKBOOK_BYTES) {
    return `${file.name} is over 50 MB.`
  }
  return null
}

/** Upload an Open CEDA workbook, optionally activating it once imported. */
export function WorkbookUpload({ importing, onUpload }: WorkbookUploadProps) {
  const [file, setFile] = React.useState<File | null>(null)
  const [activate, setActivate] = React.useState(true)
  const [progress, setProgress] = React.useState<number | null>(null)
  const [error, setError] = React.useState<string | null>(null)
  const input = React.useRef<HTMLInputElement>(null)
  const uploading = progress !== null

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (!file) {
      return
    }
    const problem = workbookProblem(file)
    if (problem) {
      setError(problem)
      return
    }
    setError(null)
    setProgress(0)
    try {
      await onUpload(file, activate, setProgress)
      setFile(null)
      if (input.current) {
        input.current.value = ''
      }
    } catch (uploadError) {
      setError(
        uploadError instanceof Error ? uploadError.message : 'Upload failed',
      )
    } finally {
      setProgress(null)
    }
  }

  return (
    <Card
      role="region"
      aria-label="Upload a workbook"
      className="flex flex-col"
    >
      <CardHeader>
        <CardTitle>Upload a workbook</CardTitle>
        <CardDescription>
          An Open CEDA .xlsx from openceda.org, up to 50 MB. It is imported in
          the background; re-uploading a release replaces it.
        </CardDescription>
      </CardHeader>
      <form
        className="flex flex-col gap-4 px-6 pb-6"
        onSubmit={(event) => {
          void submit(event)
        }}
      >
        <input
          ref={input}
          type="file"
          accept=".xlsx"
          aria-label="Workbook file"
          disabled={uploading || importing}
          className="text-sm file:mr-3 file:rounded-lg file:border file:border-border file:bg-card file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-foreground hover:file:bg-muted"
          onChange={(event) => {
            const chosen = event.target.files?.[0] ?? null
            setFile(chosen)
            setError(chosen ? workbookProblem(chosen) : null)
          }}
        />
        <label className="flex items-center gap-2 text-sm">
          <Checkbox
            checked={activate}
            onCheckedChange={(checked) => {
              setActivate(checked)
            }}
            disabled={uploading || importing}
          />
          Activate when imported
        </label>
        {uploading ? (
          <Progress
            aria-label="Upload progress"
            value={Math.round(progress * 100)}
          />
        ) : null}
        {importing ? (
          <p className="text-sm text-muted-foreground">
            A workbook is being imported. Wait for it to finish.
          </p>
        ) : null}
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        <div>
          <Button
            type="submit"
            disabled={!file || uploading || importing || error !== null}
          >
            <Upload />
            {uploading ? 'Uploading…' : 'Upload and import'}
          </Button>
        </div>
      </form>
    </Card>
  )
}
