import { describe, expect, it, vi } from 'vitest'
import { renderHook } from '@testing-library/react'
import type {
  AgreementAnalysis,
  AgreementRead,
} from '#/lib/api/agreement-types'
import { useAnalysisFinished } from './use-analysis-finished'

function withAnalysis(status: AgreementAnalysis['status']): AgreementRead {
  return {
    analysis: {
      id: 'r1',
      status,
      requested_at: '2026-09-27T10:00:00Z',
      started_at: null,
      finished_at: null,
      error: null,
    },
  } as AgreementRead
}

describe('useAnalysisFinished', () => {
  it('reports an analysis it saw running once it has finished', () => {
    const onFinished = vi.fn()
    const { rerender } = renderHook(
      ({ agreement }) => {
        useAnalysisFinished(agreement, onFinished)
      },
      { initialProps: { agreement: withAnalysis('running') } },
    )

    rerender({ agreement: withAnalysis('running') })
    expect(onFinished).not.toHaveBeenCalled()
    rerender({ agreement: withAnalysis('succeeded') })
    expect(onFinished).toHaveBeenCalledOnce()
    rerender({ agreement: withAnalysis('succeeded') })
    expect(onFinished).toHaveBeenCalledOnce()
  })

  it('stays quiet about an analysis that had already finished', () => {
    const onFinished = vi.fn()
    renderHook(() => {
      useAnalysisFinished(withAnalysis('succeeded'), onFinished)
    })

    expect(onFinished).not.toHaveBeenCalled()
  })
})
