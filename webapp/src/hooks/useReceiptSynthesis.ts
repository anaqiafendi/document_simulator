import { useCallback, useState } from 'react'
import type {
  ReceiptRenderRequest,
  ReceiptRenderResponse,
} from '../types'
import { renderReceipt as apiRenderReceipt } from '../api/client'

const DEFAULT_REQUEST: ReceiptRenderRequest = {
  template: 'thermal_minimal',
  seed: 42,
  augraphy_preset: null,
  start_stage: null,
  cached_image_id: null,
}

export interface UseReceiptSynthesis {
  request: ReceiptRenderRequest
  setRequest: (next: Partial<ReceiptRenderRequest>) => void
  response: ReceiptRenderResponse | null
  selectedStage: string
  setSelectedStage: (stage: string) => void
  showBboxes: boolean
  setShowBboxes: (v: boolean) => void
  showLabels: boolean
  setShowLabels: (v: boolean) => void
  isRendering: boolean
  error: string | null
  render: () => Promise<void>
  rerollSeed: () => void
}

export function useReceiptSynthesis(
  initial: Partial<ReceiptRenderRequest> = {},
): UseReceiptSynthesis {
  const [request, setRequestState] = useState<ReceiptRenderRequest>({
    ...DEFAULT_REQUEST,
    ...initial,
  })
  const [response, setResponse] = useState<ReceiptRenderResponse | null>(null)
  // Default the inspector to the raster stage — it has an image and is the
  // first non-content stage that always exists.
  const [selectedStage, setSelectedStage] = useState<string>('raster')
  const [showBboxes, setShowBboxes] = useState<boolean>(true)
  const [showLabels, setShowLabels] = useState<boolean>(false)
  const [isRendering, setIsRendering] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const setRequest = useCallback((next: Partial<ReceiptRenderRequest>) => {
    setRequestState(prev => ({ ...prev, ...next }))
  }, [])

  const rerollSeed = useCallback(() => {
    const seed = Math.floor(Math.random() * 1_000_000) + 1
    setRequestState(prev => ({ ...prev, seed }))
  }, [])

  const render = useCallback(async () => {
    setIsRendering(true)
    setError(null)
    try {
      const res = await apiRenderReceipt(request)
      setResponse(res)
      // If the previously selected stage isn't in the new response, fall back
      // to the last available stage with an image (or 'raster').
      const stages = res.stages.map(s => s.stage as string)
      if (!stages.includes(selectedStage)) {
        const withImage = res.stages.filter(s => s.image_b64).map(s => s.stage as string)
        setSelectedStage(withImage[withImage.length - 1] ?? 'raster')
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setIsRendering(false)
    }
  }, [request, selectedStage])

  return {
    request,
    setRequest,
    response,
    selectedStage,
    setSelectedStage,
    showBboxes,
    setShowBboxes,
    showLabels,
    setShowLabels,
    isRendering,
    error,
    render,
    rerollSeed,
  }
}
