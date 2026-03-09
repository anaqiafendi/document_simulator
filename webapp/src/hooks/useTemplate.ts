import { useEffect, useRef, useState } from 'react'
import type { TemplateInfo } from '../types'
import { listSamples, loadSample, uploadTemplate } from '../api/client'

export function useTemplate() {
  const [templateInfo, setTemplateInfo] = useState<TemplateInfo | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [samples, setSamples] = useState<string[]>([])
  const [currentPage, setCurrentPage] = useState(0)

  // Keep a reference to the last uploaded File or sample name so we can
  // re-request when the user navigates to a different page.
  const storedFile = useRef<File | null>(null)
  const storedSample = useRef<string | null>(null)

  // Load sample list on mount (best-effort — API may not be running yet)
  useEffect(() => {
    listSamples().then(setSamples).catch(() => {})
  }, [])

  const upload = async (file: File, page = 0) => {
    setLoading(true)
    setError(null)
    try {
      storedFile.current = file
      storedSample.current = null
      const info = await uploadTemplate(file, 150, page)
      setTemplateInfo(info)
      setCurrentPage(page)
    } catch (err) {
      setError(String(err))
    } finally {
      setLoading(false)
    }
  }

  const loadFromSample = async (filename: string, page = 0) => {
    setLoading(true)
    setError(null)
    try {
      storedSample.current = filename
      storedFile.current = null
      const info = await loadSample(filename, 150, page)
      setTemplateInfo(info)
      setCurrentPage(page)
    } catch (err) {
      setError(String(err))
    } finally {
      setLoading(false)
    }
  }

  const navigatePage = async (delta: number) => {
    if (!templateInfo) return
    const newPage = Math.max(0, Math.min(currentPage + delta, templateInfo.page_count - 1))
    if (newPage === currentPage) return

    if (storedFile.current) {
      await upload(storedFile.current, newPage)
    } else if (storedSample.current) {
      await loadFromSample(storedSample.current, newPage)
    }
  }

  return { templateInfo, loading, error, samples, currentPage, upload, loadFromSample, navigatePage }
}
