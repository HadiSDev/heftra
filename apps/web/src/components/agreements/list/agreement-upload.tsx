import * as React from 'react'
import { Upload } from 'lucide-react'
import {
  Button,
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
  FileDropzone,
  Progress,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '#/components/ui'

/** The largest agreement the API accepts. */
export const MAX_AGREEMENT_BYTES = 25 * 1024 * 1024

export interface UploadCompany {
  id: string
  name: string
}

export interface AgreementUploadProps {
  companies: Array<UploadCompany>
  /** The company chosen on the page, if any; asked for otherwise. */
  companyId?: string
  onUpload: (
    companyId: string,
    file: File,
    onProgress: (sent: number) => void,
  ) => Promise<void>
}

/** Drop a trade or framework agreement PDF to have it read. */
export function AgreementUpload({
  companies,
  companyId,
  onUpload,
}: AgreementUploadProps) {
  const [file, setFile] = React.useState<File | null>(null)
  const [chosenCompany, setChosenCompany] = React.useState(
    companyId ?? (companies.length === 1 ? companies[0].id : ''),
  )
  const [progress, setProgress] = React.useState<number | null>(null)
  const [error, setError] = React.useState<string | null>(null)
  const target = companyId ?? chosenCompany
  const uploading = progress !== null
  const items = companies.map((company) => ({
    value: company.id,
    label: company.name,
  }))

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (!file || !target) {
      return
    }
    setError(null)
    setProgress(0)
    try {
      await onUpload(target, file, setProgress)
      setFile(null)
    } catch (uploadError) {
      setError(
        uploadError instanceof Error ? uploadError.message : 'Upload failed',
      )
    } finally {
      setProgress(null)
    }
  }

  return (
    <Card role="region" aria-label="Upload an agreement">
      <CardHeader>
        <CardTitle>Upload an agreement</CardTitle>
        <CardDescription>
          A trade or framework agreement with a supplier. Its terms are read for
          you to confirm, then your spend is checked against them.
        </CardDescription>
      </CardHeader>
      <form
        className="flex flex-col gap-4 px-6 pb-6"
        onSubmit={(event) => {
          void submit(event)
        }}
      >
        {companyId === undefined && companies.length > 1 ? (
          <Select
            items={items}
            value={chosenCompany}
            onValueChange={(next) => {
              setChosenCompany(String(next))
            }}
          >
            <SelectTrigger aria-label="Company" className="max-w-xs">
              <SelectValue items={items} placeholder="Choose a company" />
            </SelectTrigger>
            <SelectContent>
              {items.map((item) => (
                <SelectItem key={item.value} value={item.value}>
                  {item.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : null}
        <FileDropzone
          value={file}
          onChange={(chosen) => {
            setFile(chosen)
            setError(null)
          }}
          accept=".pdf,application/pdf"
          maxBytes={MAX_AGREEMENT_BYTES}
          disabled={uploading}
          label="Agreement file"
          title="Drop an agreement PDF here"
          hint="PDF, up to 25 MB"
          error={error}
        />
        {uploading ? (
          <Progress
            aria-label="Upload progress"
            value={Math.round(progress * 100)}
          />
        ) : null}
        <div>
          <Button type="submit" disabled={!file || !target || uploading}>
            <Upload />
            {uploading ? 'Uploading…' : 'Upload and read'}
          </Button>
        </div>
      </form>
    </Card>
  )
}
