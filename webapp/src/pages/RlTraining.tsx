import { useCallback, useEffect, useRef, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { startRlTraining, getRlJobStatus, getRlMetrics, stopRlTraining } from '../api/client'
import type { RlJobStatus, RewardPoint, RlTrainConfig } from '../types'

const card: React.CSSProperties = {
  background: '#fff', borderRadius: 8, border: '1px solid #e0e0e0',
  padding: '16px 20px', marginBottom: 16,
}

const btn: React.CSSProperties = {
  padding: '8px 20px', borderRadius: 6, border: 'none', cursor: 'pointer',
  fontSize: 14, fontWeight: 600, background: '#4f6ef7', color: '#fff',
}

const btnStop: React.CSSProperties = {
  ...btn, background: '#c0392b',
}

const btnDisabled: React.CSSProperties = { ...btn, background: '#aaa', cursor: 'not-allowed' }

function NumberInput({
  label, value, onChange, step, min, max, format,
}: {
  label: string
  value: number
  onChange: (v: number) => void
  step?: number
  min?: number
  max?: number
  format?: 'float' | 'int'
}) {
  return (
    <div>
      <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 3 }}>{label}</label>
      <input
        type="number"
        value={value}
        step={step}
        min={min}
        max={max}
        onChange={e => onChange(format === 'float' ? parseFloat(e.target.value) : parseInt(e.target.value, 10))}
        style={{ fontSize: 13, padding: '5px 8px', borderRadius: 5, border: '1px solid #ccc', width: 100 }}
      />
    </div>
  )
}

export default function RlTraining() {
  const [config, setConfig] = useState<RlTrainConfig>({
    learning_rate: 3e-4,
    batch_size: 64,
    n_steps: 2048,
    num_envs: 4,
    total_timesteps: 100_000,
    checkpoint_freq: 10_000,
    dataset_dir: null,
  })

  const [jobId, setJobId] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<RlJobStatus | null>(null)
  const [rewardCurve, setRewardCurve] = useState<RewardPoint[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  const pollJob = useCallback(async (id: string) => {
    try {
      const [status, metrics] = await Promise.all([
        getRlJobStatus(id),
        getRlMetrics(id),
      ])
      setJobStatus(status)
      setRewardCurve(metrics.reward_curve)
      if (status.status === 'done' || status.status === 'failed') {
        stopPolling()
        setLoading(false)
      }
    } catch {
      stopPolling()
      setLoading(false)
    }
  }, [stopPolling])

  useEffect(() => {
    if (!jobId) return
    stopPolling()
    pollRef.current = setInterval(() => pollJob(jobId), 2000)
    return stopPolling
  }, [jobId, pollJob, stopPolling])

  const handleStart = async () => {
    setError(null)
    setJobId(null)
    setJobStatus(null)
    setRewardCurve([])
    setLoading(true)
    try {
      const id = await startRlTraining(config)
      setJobId(id)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      setLoading(false)
    }
  }

  const handleStop = async () => {
    if (!jobId) return
    await stopRlTraining(jobId)
  }

  const isRunning = loading || jobStatus?.status === 'pending' || jobStatus?.status === 'running'
  const isDone = jobStatus?.status === 'done'
  const isFailed = jobStatus?.status === 'failed'
  const progress = jobStatus?.progress ?? 0

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto', padding: '24px 24px' }}>
      <h2 style={{ margin: '0 0 4px', fontSize: 22 }}>RL Training</h2>
      <p style={{ color: '#666', margin: '0 0 20px', fontSize: 14 }}>
        Train a PPO agent to learn which augmentation parameters maximise OCR quality.
        Training runs in a background thread; the reward chart updates live.
      </p>

      <div style={card}>
        {/* Config form */}
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 14 }}>
          <NumberInput
            label="Learning rate" value={config.learning_rate}
            onChange={v => setConfig(c => ({ ...c, learning_rate: v }))}
            step={1e-5} min={1e-6} max={1} format="float"
          />
          <NumberInput
            label="Batch size" value={config.batch_size}
            onChange={v => setConfig(c => ({ ...c, batch_size: v }))}
            step={16} min={16} max={512} format="int"
          />
          <NumberInput
            label="N steps" value={config.n_steps}
            onChange={v => setConfig(c => ({ ...c, n_steps: v }))}
            step={256} min={256} max={8192} format="int"
          />
          <NumberInput
            label="Num envs" value={config.num_envs}
            onChange={v => setConfig(c => ({ ...c, num_envs: v }))}
            step={1} min={1} max={8} format="int"
          />
          <NumberInput
            label="Total timesteps" value={config.total_timesteps}
            onChange={v => setConfig(c => ({ ...c, total_timesteps: v }))}
            step={10_000} min={1_000} max={10_000_000} format="int"
          />
          <NumberInput
            label="Checkpoint freq" value={config.checkpoint_freq}
            onChange={v => setConfig(c => ({ ...c, checkpoint_freq: v }))}
            step={1_000} min={1_000} max={100_000} format="int"
          />
        </div>

        {/* Dataset dir */}
        <div style={{ marginBottom: 14 }}>
          <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 3 }}>
            Dataset directory (optional — server-side path)
          </label>
          <input
            type="text"
            placeholder="e.g. /path/to/data/train"
            value={config.dataset_dir ?? ''}
            onChange={e => setConfig(c => ({ ...c, dataset_dir: e.target.value || null }))}
            style={{ fontSize: 13, padding: '6px 10px', borderRadius: 5, border: '1px solid #ccc', width: 320 }}
          />
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          <button
            style={isRunning ? btnDisabled : btn}
            disabled={isRunning}
            onClick={handleStart}
          >
            Start Training
          </button>
          {isRunning && (
            <button style={btnStop} onClick={handleStop}>
              Stop
            </button>
          )}
        </div>

        {error && (
          <div style={{ marginTop: 12, color: '#c0392b', background: '#fdecea', padding: '8px 12px', borderRadius: 5, fontSize: 13 }}>
            {error}
          </div>
        )}
      </div>

      {/* Status + progress */}
      {jobStatus && (
        <div style={card}>
          <div style={{ display: 'flex', gap: 24, alignItems: 'center', flexWrap: 'wrap', marginBottom: 10 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>
              Status:{' '}
              <span style={{ color: isDone ? '#27ae60' : isFailed ? '#c0392b' : '#4f6ef7' }}>
                {jobStatus.status}
              </span>
            </span>
            {jobStatus.step > 0 && (
              <span style={{ fontSize: 13 }}>
                Step: <strong>{jobStatus.step.toLocaleString()}</strong> / {config.total_timesteps.toLocaleString()}
              </span>
            )}
            {jobStatus.reward !== 0 && (
              <span style={{ fontSize: 13 }}>
                Reward: <strong>{jobStatus.reward.toFixed(4)}</strong>
              </span>
            )}
          </div>
          <div style={{ background: '#f0f0f0', borderRadius: 4, height: 8, overflow: 'hidden' }}>
            <div style={{
              width: `${Math.round(progress * 100)}%`,
              height: '100%',
              background: isDone ? '#27ae60' : isFailed ? '#c0392b' : '#4f6ef7',
              transition: 'width 0.3s',
            }} />
          </div>
          {isFailed && jobStatus.error && (
            <div style={{ marginTop: 10, color: '#c0392b', fontSize: 13 }}>{jobStatus.error}</div>
          )}
          {isDone && jobStatus.model_path && (
            <div style={{ marginTop: 10, fontSize: 13, color: '#27ae60' }}>
              Model saved: <code>{jobStatus.model_path}</code>
            </div>
          )}
        </div>
      )}

      {/* Reward curve */}
      {rewardCurve.length > 0 && (
        <div style={card}>
          <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 12 }}>Reward Curve</div>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={rewardCurve} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="step"
                tickFormatter={v => `${(v / 1000).toFixed(0)}k`}
                tick={{ fontSize: 11 }}
                label={{ value: 'Step', position: 'insideBottom', offset: -4, fontSize: 12 }}
              />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(v) => [typeof v === 'number' ? v.toFixed(4) : String(v), 'Reward']}
                labelFormatter={l => `Step ${Number(l).toLocaleString()}`}
              />
              <Line
                type="monotone"
                dataKey="reward"
                stroke="#4f6ef7"
                dot={false}
                strokeWidth={2}
                name="Reward"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {!jobId && !loading && (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#bbb', fontSize: 14 }}>
          Configure training parameters above and click <strong>Start Training</strong>.
        </div>
      )}
    </div>
  )
}
