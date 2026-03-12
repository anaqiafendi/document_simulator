import { useCallback, useEffect, useRef, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { startEvaluation, getEvaluationStatus } from '../api/client'
import type { EvalJobStatus, EvalMetrics } from '../types'

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

function MetricCard({ label, value, delta }: { label: string; value: string; delta?: string }) {
  const deltaNum = delta ? parseFloat(delta) : 0
  const deltaColor = deltaNum > 0 ? '#c0392b' : deltaNum < 0 ? '#27ae60' : '#888'
  return (
    <div style={{ ...card, flex: '0 0 auto', minWidth: 140, textAlign: 'center' }}>
      <div style={{ fontSize: 11, color: '#888', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 700, color: '#333', marginTop: 4 }}>{value}</div>
      {delta && (
        <div style={{ fontSize: 12, color: deltaColor, marginTop: 2 }}>{deltaNum > 0 ? '+' : ''}{delta}</div>
      )}
    </div>
  )
}

function CerWerBarChart({ metrics }: { metrics: EvalMetrics }) {
  const data = [
    {
      name: 'CER',
      Original: parseFloat((metrics.mean_original_cer * 100).toFixed(1)),
      Augmented: parseFloat((metrics.mean_augmented_cer * 100).toFixed(1)),
    },
    {
      name: 'WER',
      Original: parseFloat((metrics.mean_original_wer * 100).toFixed(1)),
      Augmented: parseFloat((metrics.mean_augmented_wer * 100).toFixed(1)),
    },
    {
      name: 'Confidence',
      Original: parseFloat((metrics.mean_original_confidence * 100).toFixed(1)),
      Augmented: parseFloat((metrics.mean_augmented_confidence * 100).toFixed(1)),
    },
  ]
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" tick={{ fontSize: 12 }} />
        <YAxis tickFormatter={v => `${v}%`} tick={{ fontSize: 12 }} />
        <Tooltip formatter={(v) => `${v}%`} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <ReferenceLine y={100} stroke="#c0392b" strokeDasharray="4 2" label={{ value: '100%', fontSize: 10 }} />
        <Bar dataKey="Original" fill="#7b8cde" radius={[3, 3, 0, 0]} />
        <Bar dataKey="Augmented" fill="#f0965a" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

export default function Evaluation() {
  const [preset, setPreset] = useState('medium')
  const [useGpu, setUseGpu] = useState(false)
  const [zipFile, setZipFile] = useState<File | null>(null)
  const [datasetDir, setDatasetDir] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)

  const [jobId, setJobId] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<EvalJobStatus | null>(null)
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
        const status = await getEvaluationStatus(jobId)
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

  const handleRun = async () => {
    if (!zipFile && !datasetDir) return
    setError(null)
    setJobId(null)
    setJobStatus(null)
    setLoading(true)
    try {
      const id = await startEvaluation(preset, zipFile ?? undefined, datasetDir || undefined, useGpu)
      setJobId(id)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      setLoading(false)
    }
  }

  const metrics: EvalMetrics | null = (jobStatus?.status === 'done' && jobStatus.results)
    ? (jobStatus.results as EvalMetrics)
    : null

  const isRunning = loading || jobStatus?.status === 'pending' || jobStatus?.status === 'running'
  const canRun = (!!zipFile || !!datasetDir) && !isRunning

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto', padding: '24px 24px' }}>
      <h2 style={{ margin: '0 0 4px', fontSize: 22 }}>Evaluation Dashboard</h2>
      <p style={{ color: '#666', margin: '0 0 20px', fontSize: 14 }}>
        Measure CER, WER, and OCR confidence across a labelled dataset — before and after augmentation.
      </p>

      <div style={card}>
        {/* Dataset input */}
        <div style={{ marginBottom: 14 }}>
          <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 4 }}>
            Upload dataset ZIP (PDF/image + JSON pairs)
          </label>
          <input
            type="file"
            accept=".zip"
            onChange={e => {
              setZipFile(e.target.files?.[0] ?? null)
              setJobId(null)
              setJobStatus(null)
              setError(null)
            }}
            style={{ fontSize: 13 }}
          />
        </div>

        {/* Advanced: directory */}
        <div style={{ marginBottom: 14 }}>
          <button
            onClick={() => setShowAdvanced(v => !v)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 13, color: '#4f6ef7', padding: 0 }}
          >
            {showAdvanced ? '▾' : '▸'} Advanced — use local directory path
          </button>
          {showAdvanced && (
            <div style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center' }}>
              <input
                type="text"
                placeholder="e.g. /path/to/data/test"
                value={datasetDir}
                onChange={e => setDatasetDir(e.target.value)}
                style={{ fontSize: 13, padding: '6px 10px', borderRadius: 5, border: '1px solid #ccc', flex: '1 1 300px' }}
              />
            </div>
          )}
        </div>

        <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div>
            <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 3 }}>Preset</label>
            <select value={preset} onChange={e => setPreset(e.target.value)}
              style={{ fontSize: 13, padding: '5px 8px', borderRadius: 5, border: '1px solid #ccc' }}>
              {PRESETS.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, cursor: 'pointer' }}>
            <input type="checkbox" checked={useGpu} onChange={e => setUseGpu(e.target.checked)} />
            GPU for OCR
          </label>
          <button
            style={canRun ? btn : btnDisabled}
            disabled={!canRun}
            onClick={handleRun}
          >
            {isRunning ? 'Evaluating…' : 'Run Evaluation'}
          </button>
        </div>

        {error && (
          <div style={{ marginTop: 12, color: '#c0392b', background: '#fdecea', padding: '8px 12px', borderRadius: 5, fontSize: 13 }}>
            {error}
          </div>
        )}
      </div>

      {/* Status */}
      {jobStatus && jobStatus.status !== 'done' && (
        <div style={card}>
          <span style={{ fontSize: 13, fontWeight: 600 }}>
            Status:{' '}
            <span style={{ color: jobStatus.status === 'failed' ? '#c0392b' : '#4f6ef7' }}>
              {jobStatus.status}
            </span>
          </span>
          {jobStatus.status === 'failed' && jobStatus.error && (
            <div style={{ marginTop: 8, color: '#c0392b', fontSize: 13 }}>{jobStatus.error}</div>
          )}
          {(jobStatus.status === 'running' || jobStatus.status === 'pending') && (
            <div style={{ marginTop: 8, background: '#f0f0f0', borderRadius: 4, height: 6, overflow: 'hidden' }}>
              <div style={{ width: `${Math.max(Math.round(jobStatus.progress * 100), 5)}%`, height: '100%', background: '#4f6ef7', transition: 'width 0.3s' }} />
            </div>
          )}
        </div>
      )}

      {/* Results */}
      {metrics && (
        <>
          {/* Metric cards */}
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
            <MetricCard label="Samples" value={String(metrics.n_samples)} />
            <MetricCard
              label="Augmented CER"
              value={`${(metrics.mean_augmented_cer * 100).toFixed(1)}%`}
              delta={`${((metrics.mean_augmented_cer - metrics.mean_original_cer) * 100).toFixed(1)}%`}
            />
            <MetricCard
              label="Augmented WER"
              value={`${(metrics.mean_augmented_wer * 100).toFixed(1)}%`}
              delta={`${((metrics.mean_augmented_wer - metrics.mean_original_wer) * 100).toFixed(1)}%`}
            />
            <MetricCard
              label="Augmented Conf."
              value={`${(metrics.mean_augmented_confidence * 100).toFixed(1)}%`}
              delta={`${((metrics.mean_augmented_confidence - metrics.mean_original_confidence) * 100).toFixed(1)}%`}
            />
          </div>

          {/* CER/WER chart */}
          <div style={card}>
            <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 12 }}>
              Original vs Augmented Metrics
            </div>
            <CerWerBarChart metrics={metrics} />
          </div>

          {/* Summary table */}
          <div style={card}>
            <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 12 }}>Summary Statistics</div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: '#f5f5f5' }}>
                  {['Metric', 'Orig. mean', 'Orig. std', 'Aug. mean', 'Aug. std', 'Delta'].map(h => (
                    <th key={h} style={{ padding: '6px 12px', textAlign: 'left', borderBottom: '1px solid #e0e0e0', fontWeight: 600 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  {
                    name: 'CER',
                    origMean: metrics.mean_original_cer, origStd: metrics.std_original_cer,
                    augMean: metrics.mean_augmented_cer, augStd: metrics.std_augmented_cer,
                  },
                  {
                    name: 'WER',
                    origMean: metrics.mean_original_wer, origStd: metrics.std_original_wer,
                    augMean: metrics.mean_augmented_wer, augStd: metrics.std_augmented_wer,
                  },
                  {
                    name: 'Confidence',
                    origMean: metrics.mean_original_confidence, origStd: metrics.std_original_confidence,
                    augMean: metrics.mean_augmented_confidence, augStd: metrics.std_augmented_confidence,
                  },
                ].map(row => {
                  const delta = row.augMean - row.origMean
                  return (
                    <tr key={row.name} style={{ borderBottom: '1px solid #f0f0f0' }}>
                      <td style={{ padding: '6px 12px', fontWeight: 600 }}>{row.name}</td>
                      <td style={{ padding: '6px 12px' }}>{(row.origMean * 100).toFixed(1)}%</td>
                      <td style={{ padding: '6px 12px', color: '#888' }}>{(row.origStd * 100).toFixed(1)}%</td>
                      <td style={{ padding: '6px 12px' }}>{(row.augMean * 100).toFixed(1)}%</td>
                      <td style={{ padding: '6px 12px', color: '#888' }}>{(row.augStd * 100).toFixed(1)}%</td>
                      <td style={{ padding: '6px 12px', color: delta > 0 ? '#c0392b' : delta < 0 ? '#27ae60' : '#888' }}>
                        {delta > 0 ? '+' : ''}{(delta * 100).toFixed(1)}%
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </>
      )}

      {!zipFile && !datasetDir && !jobId && (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#bbb', fontSize: 14 }}>
          Upload a dataset ZIP or enter a directory path to begin.
        </div>
      )}
    </div>
  )
}
