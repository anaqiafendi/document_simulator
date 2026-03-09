import { useState } from 'react'
import type { PreviewSample, SynthesisConfig } from '../types'
import { fetchPreviews } from '../api/client'

export function usePreviews() {
  const [previews, setPreviews] = useState<PreviewSample[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadPreviews = async (config: SynthesisConfig, templateB64?: string) => {
    setLoading(true)
    setError(null)
    try {
      const samples = await fetchPreviews(config, [42, 43, 44], templateB64)
      setPreviews(samples)
    } catch (err) {
      setError(String(err))
    } finally {
      setLoading(false)
    }
  }

  const reroll = async (idx: number, config: SynthesisConfig, templateB64?: string) => {
    // Bug 2 fix: use a different random seed on every re-roll so the image
    // actually changes. Previously `1000 + idx` was always the same value,
    // making repeated re-rolls a no-op.
    const seed = Math.floor(Math.random() * 1_000_000) + 10000
    try {
      const samples = await fetchPreviews(config, [seed], templateB64)
      setPreviews(prev => {
        const next = [...prev]
        next[idx] = samples[0]
        return next
      })
    } catch (err) {
      setError(String(err))
    }
  }

  return { previews, loading, error, loadPreviews, reroll }
}
