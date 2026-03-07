import { useEffect, useState } from 'react'
import type { TemplateInfo } from '../types'
import { listSamples, loadSample, uploadTemplate } from '../api/client'

export function useTemplate() {
  const [templateInfo, setTemplateInfo] = useState<TemplateInfo | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [samples, setSamples] = useState<string[]>([])

  // Load sample list on mount (best-effort — API may not be running yet)
  useEffect(() => {
    listSamples().then(setSamples).catch(() => {})
  }, [])

  const upload = async (file: File) => {
    setLoading(true)
    setError(null)
    try {
      setTemplateInfo(await uploadTemplate(file))
    } catch (err) {
      setError(String(err))
    } finally {
      setLoading(false)
    }
  }

  const loadFromSample = async (filename: string) => {
    setLoading(true)
    setError(null)
    try {
      setTemplateInfo(await loadSample(filename))
    } catch (err) {
      setError(String(err))
    } finally {
      setLoading(false)
    }
  }

  return { templateInfo, loading, error, samples, upload, loadFromSample }
}
