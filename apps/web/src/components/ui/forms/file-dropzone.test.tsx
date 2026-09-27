import * as React from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { FileDropzone, fileRejection, formatFileSize } from './file-dropzone'

afterEach(() => {
  cleanup()
})

function Harness({
  onChange,
  maxBytes,
  disabled = false,
}: {
  onChange: (file: File | null) => void
  maxBytes?: number
  disabled?: boolean
}) {
  const [file, setFile] = React.useState<File | null>(null)
  return (
    <FileDropzone
      value={file}
      onChange={(chosen) => {
        setFile(chosen)
        onChange(chosen)
      }}
      accept=".xlsx"
      maxBytes={maxBytes}
      disabled={disabled}
      label="Workbook file"
      title="Drop a workbook here"
      hint=".xlsx, up to 50 MB"
    />
  )
}

function dropzone(): HTMLElement {
  const title = screen.getByText(/Drop a workbook here|Drop to choose it/)
  const zone = title.closest('[class*="border-dashed"]')
  if (!(zone instanceof HTMLElement)) {
    throw new Error('no dropzone')
  }
  return zone
}

describe('FileDropzone', () => {
  it('takes a dropped file and shows its name and size', () => {
    const onChange = vi.fn()
    render(<Harness onChange={onChange} />)
    const file = new File(['x'.repeat(2048)], 'ceda.xlsx')

    fireEvent.drop(dropzone(), { dataTransfer: { files: [file] } })

    expect(onChange).toHaveBeenCalledWith(file)
    expect(screen.getByText('ceda.xlsx')).toBeTruthy()
    expect(screen.getByText('2.0 KB')).toBeTruthy()
  })

  it('highlights while a file is dragged over it', () => {
    render(<Harness onChange={vi.fn()} />)

    fireEvent.dragEnter(dropzone())

    expect(screen.getByText('Drop to choose it')).toBeTruthy()
    expect(dropzone().dataset.dragging).toBe('true')
  })

  it('takes a file chosen by browsing', () => {
    const onChange = vi.fn()
    render(<Harness onChange={onChange} />)
    const file = new File(['PK'], 'ceda.xlsx')

    fireEvent.change(screen.getByLabelText('Workbook file'), {
      target: { files: [file] },
    })

    expect(onChange).toHaveBeenCalledWith(file)
  })

  it('refuses a file of another type, saying why', () => {
    const onChange = vi.fn()
    render(<Harness onChange={onChange} />)

    fireEvent.drop(dropzone(), {
      dataTransfer: { files: [new File(['%PDF'], 'invoice.pdf')] },
    })

    expect(onChange).toHaveBeenCalledWith(null)
    expect(screen.getByRole('alert').textContent).toBe(
      "invoice.pdf isn't an accepted file (.xlsx).",
    )
  })

  it('removes the chosen file', () => {
    const onChange = vi.fn()
    render(<Harness onChange={onChange} />)
    fireEvent.drop(dropzone(), {
      dataTransfer: { files: [new File(['PK'], 'ceda.xlsx')] },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Remove ceda.xlsx' }))

    expect(onChange).toHaveBeenLastCalledWith(null)
    expect(screen.getByText('Drop a workbook here')).toBeTruthy()
  })

  it('ignores drops while disabled', () => {
    const onChange = vi.fn()
    render(<Harness onChange={onChange} disabled />)

    fireEvent.drop(dropzone(), {
      dataTransfer: { files: [new File(['PK'], 'ceda.xlsx')] },
    })

    expect(onChange).not.toHaveBeenCalled()
  })
})

describe('fileRejection', () => {
  it('refuses a file over the limit', () => {
    const file = new File(['x'.repeat(3 * 1024 * 1024)], 'big.xlsx')

    expect(fileRejection(file, '.xlsx', 1024 * 1024)).toBe(
      'big.xlsx is 3.0 MB, over the 1.0 MB limit.',
    )
  })

  it('matches media types and wildcards', () => {
    const image = new File(['x'], 'photo.png', { type: 'image/png' })

    expect(fileRejection(image, 'image/*', undefined)).toBeNull()
    expect(fileRejection(image, 'application/pdf', undefined)).not.toBeNull()
  })
})

describe('formatFileSize', () => {
  it('uses the largest whole unit', () => {
    expect(formatFileSize(512)).toBe('512 B')
    expect(formatFileSize(50 * 1024 * 1024)).toBe('50 MB')
  })
})
