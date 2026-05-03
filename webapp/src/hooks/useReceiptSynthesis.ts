import { useCallback, useEffect, useRef, useState } from 'react'
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
  // ── v0.3 additions ──
  render_3d: false,
  hdri_id: null,
  curl_strength: 0.1,
}

/** When the render takes longer than this, we surface the long-render hint. */
const LONG_RENDER_HINT_MS = 2000

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
  /** Becomes true after ~2s of waiting on a 3D render. Used to surface the
   *  "Rendering 3D scene… (this can take 5-15s)" hint. */
  showLongRenderHint: boolean
  error: string | null
  render: () => Promise<void>
  rerollSeed: () => void
  /** Toggle the 3D-render flag on the next request. When turning it off we
   *  also clear hdri_id so the next request matches the v0.2 wire shape. */
  enable3DToggle: () => void
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
  const [showLongRenderHint, setShowLongRenderHint] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  // Track the long-render timer so we can clear it on unmount / new render.
  const longRenderTimer = useRef<number | null>(null)
  useEffect(() => {
    return () => {
      if (longRenderTimer.current !== null) {
        window.clearTimeout(longRenderTimer.current)
      }
    }
  }, [])

  const setRequest = useCallback((next: Partial<ReceiptRenderRequest>) => {
    setRequestState(prev => ({ ...prev, ...next }))
  }, [])

  const rerollSeed = useCallback(() => {
    const seed = Math.floor(Math.random() * 1_000_000) + 1
    setRequestState(prev => ({ ...prev, seed }))
  }, [])

  const enable3DToggle = useCallback(() => {
    setRequestState(prev => {
      const nextOn = !(prev.render_3d ?? false)
      if (nextOn) {
        return { ...prev, render_3d: true }
      }
      // Turning off — also clear hdri_id so wire payload matches v0.2 shape.
      return { ...prev, render_3d: false, hdri_id: null }
    })
  }, [])

  const render = useCallback(async () => {
    setIsRendering(true)
    setShowLongRenderHint(false)
    setError(null)

    // Schedule the long-render hint. Show it for any render — but it really
    // only matters for the 3D path (which is the only one that takes 5-15s).
    if (longRenderTimer.current !== null) {
      window.clearTimeout(longRenderTimer.current)
    }
    longRenderTimer.current = window.setTimeout(() => {
      setShowLongRenderHint(true)
    }, LONG_RENDER_HINT_MS)

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
      if (longRenderTimer.current !== null) {
        window.clearTimeout(longRenderTimer.current)
        longRenderTimer.current = null
      }
      setShowLongRenderHint(false)
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
    showLongRenderHint,
    error,
    render,
    rerollSeed,
    enable3DToggle,
  }
}
