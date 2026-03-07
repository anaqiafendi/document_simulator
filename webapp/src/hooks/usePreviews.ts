import { useState } from 'react'
import type { PreviewSample, SynthesisConfig } from '../types'
import { fetchPreviews } from '../api/client'

export function usePreviews() {
  const [previews, setPreviews] = useState<PreviewSample[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadPreviews = async (config: SynthesisConfig) => {
    setLoading(true)
    setError(null)
    try {
      const samples = await fetchPreviews(config)
      setPreviews(samples)
    } catch (err) {
      setError(String(err))
    } finally {
      setLoading(false)
    }
  }

  const reroll = async (idx: number, config: SynthesisConfig) => {
    try {
      const samples = await fetchPreviews(config, [1000 + idx])
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
