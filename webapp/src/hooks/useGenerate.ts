import { useState } from 'react'
import type { JobStatus, SynthesisConfig } from '../types'
import { startGenerate, getJobStatus, downloadUrl } from '../api/client'

export function useGenerate() {
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [downloadJobId, setDownloadJobId] = useState<string | null>(null)

  const generate = async (config: SynthesisConfig, n: number) => {
    setLoading(true)
    setError(null)
    setJobStatus(null)
    setDownloadJobId(null)
    try {
      const jobId = await startGenerate(config, n)
      const poll = setInterval(async () => {
        try {
          const status = await getJobStatus(jobId)
          setJobStatus(status)
          if (status.status === 'done') {
            clearInterval(poll)
            setDownloadJobId(jobId)
            setLoading(false)
          } else if (status.status === 'failed') {
            clearInterval(poll)
            setError(status.error ?? 'Generation failed')
            setLoading(false)
          }
        } catch (err) {
          clearInterval(poll)
          setError(String(err))
          setLoading(false)
        }
      }, 2000)
    } catch (err) {
      setError(String(err))
      setLoading(false)
    }
  }

  return { jobStatus, loading, error, downloadJobId, generate, downloadUrl }
}
