import { useCallback, useEffect, useRef, useState } from 'react'
import { startBatchProcess, getBatchJobStatus, batchDownloadUrl } from '../api/client'
import type { BatchJobStatus, BatchMode } from '../types'

const card: React.CSSProperties = {
  background: '#fff', borderRadius: 8, border: '1px solid #e0e0e0',
  padding: '16px 20px', marginBottom: 16,
}

const btn: React.CSSProperties = {
  padding: '8px 20px', borderRadius: 6, border: 'none', cursor: 'pointer',
  fontSize: 14, fontWeight: 600, background: '#4f6ef7', color: '#fff',
}

const btnDisabled: React.CSSProperties = { ...btn, background: '#aaa', cursor: 'not-allowed' }

const PRESETS = ['light', 'medium', 'heavy', 'default']

const MODE_LABELS: Record<BatchMode, string> = {
  single: 'Single template (1 copy per image)',
  per_template: 'N×M (M copies per image)',
  random_sample: 'M-total (random sample)',
}

export default function BatchProcessing() {
  const [files, setFiles] = useState<File[]>([])
  const [preset, setPreset] = useState('medium')
  const [mode, setMode] = useState<BatchMode>('single')
  const [copiesPerTemplate, setCopiesPerTemplate] = useState(3)
  const [totalOutputs, setTotalOutputs] = useState(20)
  const [seed, setSeed] = useState(0)
  const [nWorkers, setNWorkers] = useState(4)

  const [jobId, setJobId] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<BatchJobStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!jobId) return
    stopPolling()
    pollRef.current = setInterval(async () => {
      try {
        const status = await getBatchJobStatus(jobId)
        setJobStatus(status)
        if (status.status === 'done' || status.status === 'failed') {
          stopPolling()
          setLoading(false)
        }
      } catch {
        stopPolling()
        setLoading(false)
      }
    }, 2000)
    return stopPolling
  }, [jobId, stopPolling])

  const handleStart = async () => {
    if (files.length === 0) return
    setError(null)
    setJobStatus(null)
    setJobId(null)
    setLoading(true)
    try {
      const id = await startBatchProcess(files, {
        preset, mode,
        copiesPerTemplate,
        totalOutputs,
        seed,
        nWorkers,
      })
      setJobId(id)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      setLoading(false)
    }
  }

  const isDone = jobStatus?.status === 'done'
  const isFailed = jobStatus?.status === 'failed'
  const isRunning = loading || (jobStatus?.status === 'pending') || (jobStatus?.status === 'running')

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '24px 24px' }}>
      <h2 style={{ margin: '0 0 4px', fontSize: 22 }}>Batch Processing</h2>
      <p style={{ color: '#666', margin: '0 0 20px', fontSize: 14 }}>
        Augment multiple document images at once and download the results as a ZIP.
      </p>

      <div style={card}>
        {/* File upload */}
        <div style={{ marginBottom: 14 }}>
          <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 4 }}>
            Upload documents
          </label>
          <input
            type="file"
            accept=".png,.jpg,.jpeg,.bmp,.tiff"
            multiple
            onChange={e => {
              setFiles(Array.from(e.target.files ?? []))
              setJobId(null)
              setJobStatus(null)
              setError(null)
            }}
            style={{ fontSize: 13 }}
          />
          {files.length > 0 && (
            <span style={{ fontSize: 12, color: '#666', marginLeft: 8 }}>
              {files.length} file{files.length !== 1 ? 's' : ''} selected
            </span>
          )}
        </div>

        {/* Config row */}
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 14 }}>
          <div>
            <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 3 }}>Preset</label>
            <select value={preset} onChange={e => setPreset(e.target.value)}
              style={{ fontSize: 13, padding: '5px 8px', borderRadius: 5, border: '1px solid #ccc' }}>
              {PRESETS.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 3 }}>Mode</label>
            <select value={mode} onChange={e => setMode(e.target.value as BatchMode)}
              style={{ fontSize: 13, padding: '5px 8px', borderRadius: 5, border: '1px solid #ccc' }}>
              {(Object.keys(MODE_LABELS) as BatchMode[]).map(m => (
                <option key={m} value={m}>{MODE_LABELS[m]}</option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 3 }}>Workers</label>
            <input type="number" value={nWorkers} min={1} max={8} onChange={e => setNWorkers(Number(e.target.value))}
              style={{ fontSize: 13, padding: '5px 8px', borderRadius: 5, border: '1px solid #ccc', width: 60 }} />
          </div>

          {mode === 'per_template' && (
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 3 }}>Copies per template</label>
              <input type="number" value={copiesPerTemplate} min={1} max={100} onChange={e => setCopiesPerTemplate(Number(e.target.value))}
                style={{ fontSize: 13, padding: '5px 8px', borderRadius: 5, border: '1px solid #ccc', width: 80 }} />
            </div>
          )}
          {mode === 'random_sample' && (
            <>
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 3 }}>Total outputs</label>
                <input type="number" value={totalOutputs} min={1} max={500} onChange={e => setTotalOutputs(Number(e.target.value))}
                  style={{ fontSize: 13, padding: '5px 8px', borderRadius: 5, border: '1px solid #ccc', width: 80 }} />
              </div>
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 3 }}>Seed (0=random)</label>
                <input type="number" value={seed} min={0} onChange={e => setSeed(Number(e.target.value))}
                  style={{ fontSize: 13, padding: '5px 8px', borderRadius: 5, border: '1px solid #ccc', width: 80 }} />
              </div>
            </>
          )}
        </div>

        <button
          style={isRunning || files.length === 0 ? btnDisabled : btn}
          disabled={isRunning || files.length === 0}
          onClick={handleStart}
        >
          {isRunning ? 'Processing…' : 'Run Batch Augmentation'}
        </button>

        {error && (
          <div style={{ marginTop: 12, color: '#c0392b', background: '#fdecea', padding: '8px 12px', borderRadius: 5, fontSize: 13 }}>
            {error}
          </div>
        )}
      </div>

      {/* Progress */}
      {jobStatus && (
        <div style={card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>
              Status: <span style={{ color: isDone ? '#27ae60' : isFailed ? '#c0392b' : '#4f6ef7' }}>
                {jobStatus.status}
              </span>
            </span>
            <span style={{ fontSize: 13, color: '#888' }}>
              {Math.round(jobStatus.progress * 100)}%
            </span>
          </div>

          {/* Progress bar */}
          <div style={{ background: '#f0f0f0', borderRadius: 4, height: 8, overflow: 'hidden' }}>
            <div style={{
              width: `${Math.round(jobStatus.progress * 100)}%`,
              height: '100%',
              background: isDone ? '#27ae60' : isFailed ? '#c0392b' : '#4f6ef7',
              transition: 'width 0.3s',
            }} />
          </div>

          {isFailed && jobStatus.error && (
            <div style={{ marginTop: 10, color: '#c0392b', fontSize: 13 }}>
              Error: {jobStatus.error}
            </div>
          )}

          {isDone && jobId && (
            <div style={{ marginTop: 12 }}>
              <a
                href={batchDownloadUrl(jobId)}
                download="augmented_batch.zip"
                style={{ ...btn, display: 'inline-block', textDecoration: 'none' }}
              >
                Download ZIP
              </a>
            </div>
          )}
        </div>
      )}

      {files.length === 0 && !jobId && (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#bbb', fontSize: 14 }}>
          Upload document images to begin.
        </div>
      )}
    </div>
  )
}
