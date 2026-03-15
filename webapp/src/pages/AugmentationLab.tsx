import { useEffect, useRef, useState } from 'react'
import {
  augmentImage, listPresets,
  listCatalogue, augmentCatalogue, previewCatalogue, applyPipeline,
  listAugSamples, augSampleRawUrl,
  startCatalogueBatch, getCatalogueBatchStatus, catalogueBatchDownloadUrl,
} from '../api/client'
import type { AugmentResult, CatalogueEntry, CatalogueAugmentResult, PipelineResult } from '../types'
import type { CatalogueBatchStatus } from '../api/client'

// ── Shared: load a sample template (augmentation_lab dir) and convert to File ─

async function augSampleToFile(filename: string): Promise<File> {
  // Fetch the raw file (PDF or image) so the backend can render it at its own DPI
  const blob = await fetch(augSampleRawUrl(filename)).then(r => r.blob())
  const mime = filename.toLowerCase().endsWith('.pdf') ? 'application/pdf' : blob.type || 'image/png'
  return new File([blob], filename, { type: mime })
}

// ── Lightbox ──────────────────────────────────────────────────────────────────

function Lightbox({ src, title, onClose }: { src: string; title?: string; onClose: () => void }) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 9999,
        background: 'rgba(0,0,0,0.85)',
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        cursor: 'zoom-out',
      }}
    >
      {title && (
        <div style={{ color: '#fff', fontSize: 14, fontWeight: 600, marginBottom: 12, opacity: 0.85 }}>
          {title} — click or press Esc to close
        </div>
      )}
      <img
        src={src}
        alt={title}
        onClick={e => e.stopPropagation()}
        style={{
          maxWidth: '92vw', maxHeight: '88vh',
          objectFit: 'contain', borderRadius: 6,
          boxShadow: '0 4px 40px rgba(0,0,0,0.6)',
          cursor: 'default',
        }}
      />
    </div>
  )
}

// Clickable image that opens in lightbox
function LightboxImage({ src, alt, style }: { src: string; alt: string; style?: React.CSSProperties }) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <img
        src={src} alt={alt}
        onClick={() => setOpen(true)}
        style={{ cursor: 'zoom-in', ...style }}
      />
      {open && <Lightbox src={src} title={alt} onClose={() => setOpen(false)} />}
    </>
  )
}

// ── Shared: ImageSourceSelector (uses augmentation_lab samples) ───────────────

function ImageSourceSelector({
  file, onFile,
}: {
  file: File | null
  onFile: (f: File | null) => void
}) {
  const [samples, setSamples] = useState<string[]>([])
  const [loadingSample, setLoadingSample] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    listAugSamples().catch(() => []).then(s => setSamples(Array.isArray(s) ? s : []))
  }, [])

  const handleSample = async (name: string) => {
    if (!name) return
    setLoadingSample(true)
    try { onFile(await augSampleToFile(name)) }
    catch { /* ignore */ }
    finally { setLoadingSample(false) }
  }

  return (
    <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', flexWrap: 'wrap' }}>
      <div>
        <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 4 }}>Upload image</label>
        <input ref={fileRef} type="file" accept=".png,.jpg,.jpeg,.bmp,.tiff,.pdf"
          onChange={e => onFile(e.target.files?.[0] ?? null)}
          style={{ fontSize: 13 }} />
      </div>
      {samples.length > 0 && (
        <div>
          <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 4 }}>
            — or load template
          </label>
          <select defaultValue="" onChange={e => handleSample(e.target.value)}
            style={{ fontSize: 13, padding: '6px 10px', borderRadius: 5, border: '1px solid #ccc', maxWidth: 240 }}>
            <option value="" disabled>Select sample…</option>
            {samples.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          {loadingSample && <span style={{ marginLeft: 8, fontSize: 12, color: '#888' }}>Loading…</span>}
        </div>
      )}
      {file && (
        <div style={{ fontSize: 12, color: '#555', alignSelf: 'center' }}>
          <strong>{file.name}</strong> ({(file.size / 1024).toFixed(0)} KB)
        </div>
      )}
    </div>
  )
}

// ── Styles ────────────────────────────────────────────────────────────────────

const card: React.CSSProperties = {
  background: '#fff', borderRadius: 8, border: '1px solid #e0e0e0',
  padding: '16px 20px', marginBottom: 16,
}

const btn: React.CSSProperties = {
  padding: '8px 20px', borderRadius: 6, border: 'none', cursor: 'pointer',
  fontSize: 14, fontWeight: 600, background: '#4f6ef7', color: '#fff',
}

const btnSm: React.CSSProperties = { ...btn, padding: '4px 12px', fontSize: 12 }

const btnDisabled: React.CSSProperties = { ...btn, background: '#aaa', cursor: 'not-allowed' }

const PHASE_COLORS: Record<string, string> = { ink: '#6c3483', paper: '#1a6648', post: '#1a3a6b' }
const PHASE_BG: Record<string, string> = { ink: '#f5eef8', paper: '#eafaf1', post: '#eaf0fb' }

// ── Dual-handle range slider ──────────────────────────────────────────────────
// Uses document-level mousemove/mouseup listeners for drag tracking.
// Both handles are always independently grabbable — no pointer capture,
// no overlapping inputs, no z-index fighting.

function DualRangeSlider({
  label, rangeMin, rangeMax, step, value, onChange,
}: {
  label: string
  rangeMin: number
  rangeMax: number
  step: number
  value: [number, number]
  onChange: (v: [number, number]) => void
}) {
  const [lo, hi] = value
  const trackRef = useRef<HTMLDivElement>(null)
  const dragging = useRef<'lo' | 'hi' | null>(null)
  // Keep latest values in refs so document-level handlers don't use stale closures
  const loRef = useRef(lo)
  const hiRef = useRef(hi)
  const onChangeRef = useRef(onChange)
  loRef.current = lo
  hiRef.current = hi
  onChangeRef.current = onChange

  const fmt = (v: number) => step < 1 ? v.toFixed(2) : String(v)
  const pct = (v: number) => ((v - rangeMin) / (rangeMax - rangeMin)) * 100

  const snapToStep = (raw: number) => Math.round(raw / step) * step

  const xToValue = (clientX: number): number => {
    if (!trackRef.current) return loRef.current
    const rect = trackRef.current.getBoundingClientRect()
    const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width))
    return snapToStep(rangeMin + ratio * (rangeMax - rangeMin))
  }

  // Attach document-level listeners once — refs avoid re-subscribing on value changes
  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!dragging.current) return
      const v = xToValue(e.clientX)
      if (dragging.current === 'lo')
        onChangeRef.current([Math.min(Math.max(v, rangeMin), hiRef.current - step), hiRef.current])
      else
        onChangeRef.current([loRef.current, Math.max(Math.min(v, rangeMax), loRef.current + step)])
    }
    const onUp = () => { dragging.current = null }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
    return () => {
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
    }
  }, [rangeMin, rangeMax, step]) // eslint-disable-line react-hooks/exhaustive-deps

  const onThumbMouseDown = (which: 'lo' | 'hi') => (e: React.MouseEvent) => {
    e.preventDefault()
    dragging.current = which
  }

  // Track-background click snaps the nearest thumb to the click position
  const onTrackClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const v = xToValue(e.clientX)
    if (Math.abs(v - loRef.current) <= Math.abs(v - hiRef.current))
      onChange([Math.min(Math.max(v, rangeMin), hiRef.current - step), hiRef.current])
    else
      onChange([loRef.current, Math.max(Math.min(v, rangeMax), loRef.current + step)])
  }

  const thumbBase: React.CSSProperties = {
    position: 'absolute', top: '50%',
    width: 18, height: 18, borderRadius: '50%',
    background: '#4f6ef7', border: '2px solid #fff',
    boxShadow: '0 1px 5px rgba(0,0,0,0.3)',
    transform: 'translateY(-50%)',
    cursor: 'grab',
  }

  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: '#555' }}>{label}</span>
        <span style={{ fontSize: 12, color: '#4f6ef7', fontWeight: 600 }}>{fmt(lo)} – {fmt(hi)}</span>
      </div>
      {/* Track container */}
      <div ref={trackRef} onClick={onTrackClick} style={{ position: 'relative', height: 28, cursor: 'pointer' }}>
        {/* Background track */}
        <div style={{
          position: 'absolute', top: '50%', left: 0, right: 0,
          height: 4, background: '#dde', borderRadius: 2, transform: 'translateY(-50%)',
          pointerEvents: 'none',
        }} />
        {/* Filled segment */}
        <div style={{
          position: 'absolute', top: '50%',
          left: `${pct(lo)}%`, width: `${Math.max(0, pct(hi) - pct(lo))}%`,
          height: 4, background: '#4f6ef7', borderRadius: 2, transform: 'translateY(-50%)',
          pointerEvents: 'none',
        }} />
        {/* Lo thumb — slightly left of center so hi thumb is on top when overlapping */}
        <div
          onMouseDown={onThumbMouseDown('lo')}
          style={{ ...thumbBase, left: `${pct(lo)}%`, marginLeft: -10, zIndex: 2 }}
        />
        {/* Hi thumb */}
        <div
          onMouseDown={onThumbMouseDown('hi')}
          style={{ ...thumbBase, left: `${pct(hi)}%`, marginLeft: -8, zIndex: 3 }}
        />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#aaa', marginTop: 2 }}>
        <span>{fmt(rangeMin)}</span><span>{fmt(rangeMax)}</span>
      </div>
    </div>
  )
}

// ── Parameter controls for catalogue augmentations ────────────────────────────

type AugParams = Record<string, unknown>

function ParamControls({
  entry, params, onChange,
}: {
  entry: CatalogueEntry
  params: AugParams
  onChange: (p: AugParams) => void
}) {
  const dp = entry.default_params
  const get = (key: string, fallback: unknown) => (key in params ? params[key] : (key in dp ? dp[key] : fallback))

  const set = (key: string, val: unknown) => onChange({ ...params, [key]: val })

  const RangeRow = ({ k, label, min, max, step }: { k: string; label: string; min: number; max: number; step: number }) => {
    const raw = get(k, dp[k])
    const arr = Array.isArray(raw) && raw.length >= 2 ? raw : [min, max]
    const lo = isFinite(Number(arr[0])) ? Number(arr[0]) : min
    const hi = isFinite(Number(arr[1])) ? Number(arr[1]) : max
    return (
      <DualRangeSlider
        label={label} rangeMin={min} rangeMax={max} step={step}
        value={[Math.max(min, Math.min(lo, max)), Math.max(min, Math.min(hi, max))]}
        onChange={v => set(k, v)}
      />
    )
  }

  const SingleSlider = ({ k, label, min, max, step }: { k: string; label: string; min: number; max: number; step: number }) => {
    const val = get(k, dp[k]) as number
    return (
      <div style={{ marginBottom: 10 }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: '#555', minWidth: 120 }}>{label}</label>
          <input type="range" min={min} max={max} step={step} value={val}
            onChange={e => set(k, parseFloat(e.target.value))} style={{ flex: 1 }} />
          <span style={{ fontSize: 11, minWidth: 32 }}>{typeof val === 'number' ? val.toFixed(step < 1 ? 2 : 0) : val}</span>
        </div>
      </div>
    )
  }

  const SelectRow = ({ k, label, options }: { k: string; label: string; options: string[] }) => {
    const val = get(k, dp[k]) as string
    return (
      <div style={{ marginBottom: 10, display: 'flex', gap: 8, alignItems: 'center' }}>
        <label style={{ fontSize: 12, fontWeight: 600, color: '#555', minWidth: 120 }}>{label}</label>
        <select value={val} onChange={e => set(k, e.target.value)}
          style={{ fontSize: 12, padding: '3px 8px', borderRadius: 4, border: '1px solid #ccc' }}>
          {options.map(o => <option key={o} value={o}>{o}</option>)}
        </select>
      </div>
    )
  }

  const n = entry.name

  // Specific controls per augmentation type
  if (n === 'InkBleed' || n === 'BleedThrough') {
    return <RangeRow k="intensity_range" label="Intensity range" min={0} max={1} step={0.05} />
  }
  if (n === 'Markup') {
    return <>
      <SelectRow k="markup_type" label="Type" options={['strikethrough', 'crossed', 'highlight', 'underline']} />
      <RangeRow k="num_lines_range" label="Lines range" min={1} max={20} step={1} />
    </>
  }
  if (n === 'InkShifter') {
    return <RangeRow k="text_shift_scale_range" label="Shift scale" min={1} max={100} step={1} />
  }
  if (n === 'Letterpress') {
    return <>
      <RangeRow k="n_samples" label="Sample points" min={50} max={1000} step={10} />
      <RangeRow k="n_clusters" label="Clusters" min={100} max={1000} step={10} />
    </>
  }
  if (n === 'ShadowCast') {
    return <>
      <SelectRow k="shadow_side" label="Shadow side" options={['left', 'right', 'top', 'bottom']} />
      <RangeRow k="shadow_opacity_range" label="Opacity range" min={0.1} max={1.0} step={0.05} />
    </>
  }
  if (n === 'NoiseTexturize') {
    return <>
      <RangeRow k="sigma_range" label="Sigma range" min={1} max={20} step={1} />
      <RangeRow k="turbulence_range" label="Turbulence range" min={1} max={10} step={0.5} />
    </>
  }
  if (n === 'ColorShift') {
    const offX = get('color_shift_offset_x_range', dp['color_shift_offset_x_range']) as [number, number]
    const iters = get('color_shift_iterations', dp['color_shift_iterations']) as [number, number]
    return <>
      <div style={{ marginBottom: 10 }}>
        <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4, color: '#555' }}>Offset max (px)</div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <input type="range" min={1} max={50} step={1} value={offX[1]}
            onChange={e => {
              const v = parseInt(e.target.value)
              set('color_shift_offset_x_range', [1, v])
              set('color_shift_offset_y_range', [1, v])
            }} style={{ flex: 1 }} />
          <span style={{ fontSize: 11, minWidth: 24 }}>{offX[1]}</span>
        </div>
      </div>
      <div style={{ marginBottom: 10 }}>
        <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4, color: '#555' }}>Iterations max</div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <input type="range" min={1} max={8} step={1} value={iters[1]}
            onChange={e => set('color_shift_iterations', [1, parseInt(e.target.value)])} style={{ flex: 1 }} />
          <span style={{ fontSize: 11, minWidth: 24 }}>{iters[1]}</span>
        </div>
      </div>
    </>
  }
  if (n === 'DirtyDrum') {
    return <RangeRow k="line_width_range" label="Line width" min={1} max={8} step={1} />
  }
  if (n === 'Brightness') {
    return <RangeRow k="brightness_range" label="Brightness range" min={0.1} max={2.0} step={0.05} />
  }
  if (n === 'Gamma') {
    return <RangeRow k="gamma_range" label="Gamma range" min={0.5} max={3.0} step={0.1} />
  }
  if (n === 'Jpeg') {
    return <RangeRow k="quality_range" label="Quality range" min={1} max={95} step={1} />
  }
  if (n === 'LowLightNoise') {
    return <RangeRow k="low_light_range" label="Low light range" min={0.1} max={1.0} step={0.05} />
  }
  if (n === 'SubtleNoise') {
    return <SingleSlider k="subtle_range" label="Noise range" min={1} max={20} step={1} />
  }
  if (n === 'Folding') {
    // fold_count is a scalar integer, not a range
    return <SingleSlider k="fold_count" label="Fold count" min={1} max={6} step={1} />
  }
  if (n === 'Geometric') {
    return <RangeRow k="rotate_range" label="Rotate range (deg)" min={-45} max={45} step={1} />
  }

  // Generic fallback: show any numeric range params as dual sliders
  const rangeKeys = Object.entries(dp).filter(([, v]) => Array.isArray(v) && v.length === 2 && typeof v[0] === 'number')
  if (rangeKeys.length === 0) {
    return <div style={{ fontSize: 12, color: '#888', fontStyle: 'italic' }}>No tunable parameters.</div>
  }
  return (
    <>
      {rangeKeys.map(([k, v]) => {
        const arr = v as [number, number]
        const isFloat = arr[0] % 1 !== 0 || arr[1] % 1 !== 0
        // Support negative ranges (e.g. rotate_range: (-10, 10))
        const sliderMin = arr[0] < 0 ? arr[0] * 2 : 0
        const sliderMax = Math.max(Math.abs(arr[1]) * 2, 1)
        return (
          <RangeRow key={k} k={k} label={k.replace(/_/g, ' ')}
            min={sliderMin} max={sliderMax} step={isFloat ? 0.05 : 1} />
        )
      })}
    </>
  )
}

// ── Preset tab ────────────────────────────────────────────────────────────────

function PresetTab() {
  const [presets, setPresets] = useState<string[]>([])
  const [preset, setPreset] = useState('medium')
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<AugmentResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showResult, setShowResult] = useState(false)

  useEffect(() => {
    listPresets().then(setPresets).catch(() => setPresets(['light', 'medium', 'heavy', 'default']))
  }, [])

  const handleAugment = async () => {
    if (!file) return
    setLoading(true); setError(null)
    try {
      setResult(await augmentImage(file, preset))
      setShowResult(true)  // auto-expand when result arrives
    }
    catch (e: unknown) { setError(e instanceof Error ? e.message : 'Unknown error') }
    finally { setLoading(false) }
  }

  return (
    <>
      <div style={card}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <ImageSourceSelector file={file} onFile={f => { setFile(f); setResult(null); setShowResult(false); setError(null) }} />
          <div>
            <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 4 }}>Preset</label>
            <select value={preset} onChange={e => setPreset(e.target.value)}
              style={{ fontSize: 13, padding: '6px 10px', borderRadius: 5, border: '1px solid #ccc' }}>
              {(presets.length > 0 ? presets : ['light', 'medium', 'heavy', 'default']).map(p => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
          <button style={loading || !file ? btnDisabled : btn} disabled={loading || !file} onClick={handleAugment}>
            {loading ? 'Augmenting…' : 'Augment'}
          </button>
        </div>
        {error && <div style={{ marginTop: 12, color: '#c0392b', background: '#fdecea', padding: '8px 12px', borderRadius: 5, fontSize: 13 }}>{error}</div>}
      </div>

      {!file && (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#bbb', fontSize: 14 }}>Upload a document image to begin.</div>
      )}

      {/* Collapsible result section */}
      {file && (
        <div style={{ marginBottom: 16 }}>
          <button
            onClick={() => setShowResult(v => !v)}
            style={{
              display: 'flex', alignItems: 'center', gap: 8, width: '100%',
              padding: '10px 16px', borderRadius: 6, border: '1px solid #dde',
              background: showResult ? '#f0f4ff' : '#fafafa', cursor: 'pointer',
              fontSize: 13, fontWeight: 600, color: '#4f6ef7', textAlign: 'left',
            }}
          >
            <span style={{ fontSize: 16 }}>{showResult ? '▼' : '▶'}</span>
            {result ? `Result — ${result.metadata.preset} preset` : 'Result (run Augment to generate)'}
          </button>

          {showResult && (
            <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', marginTop: 12 }}>
              <div style={{ ...card, flex: '1 1 300px', marginBottom: 0 }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#888', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Original</div>
                <LightboxImage
                  src={result ? `data:image/png;base64,${result.original_b64}` : URL.createObjectURL(file)}
                  alt="Original" style={{ width: '100%', borderRadius: 4, border: '1px solid #eee' }} />
              </div>
              {result && (
                <div style={{ ...card, flex: '1 1 300px', marginBottom: 0 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: '#888', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Augmented — {result.metadata.preset}
                    </div>
                    <button style={btnSm} onClick={() => {
                      const a = document.createElement('a'); a.href = `data:image/png;base64,${result.augmented_b64}`
                      a.download = `augmented_${preset}.png`; a.click()
                    }}>Download PNG</button>
                  </div>
                  <LightboxImage src={`data:image/png;base64,${result.augmented_b64}`} alt={`Augmented — ${result.metadata.preset}`}
                    style={{ width: '100%', borderRadius: 4, border: '1px solid #eee' }} />
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </>
  )
}

// ── Catalogue tab ─────────────────────────────────────────────────────────────

function CatalogueTab() {
  const [entries, setEntries] = useState<CatalogueEntry[]>([])
  const [phase, setPhase] = useState<'all' | 'ink' | 'paper' | 'post'>('all')
  const [file, setFile] = useState<File | null>(null)
  // Multi-select: set of enabled aug names
  const [enabled, setEnabled] = useState<Set<string>>(new Set())
  // Per-aug param overrides
  const [augParams, setAugParams] = useState<Record<string, AugParams>>({})
  // Per-card expanded state (params section)
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  // Per-card thumbnail previews
  const [thumbnails, setThumbnails] = useState<Record<string, string>>({})
  const [loadingThumb, setLoadingThumb] = useState<Set<string>>(new Set())
  // Pipeline result (multi-aug apply)
  const [pipelineResult, setPipelineResult] = useState<PipelineResult | null>(null)
  // Single-aug result
  const [singleResult, setSingleResult] = useState<CatalogueAugmentResult | null>(null)
  const [loadingPipeline, setLoadingPipeline] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loadingCatalogue, setLoadingCatalogue] = useState(true)

  useEffect(() => {
    listCatalogue()
      .then(setEntries)
      .catch(() => setError('Failed to load catalogue'))
      .finally(() => setLoadingCatalogue(false))
  }, [])

  const [showResult, setShowResult] = useState(false)

  // Concurrency-limited preview queue — max 4 in-flight (thread pool backend handles it)
  const previewQueue = useRef<string[]>([])
  const activeCount = useRef(0)
  const fileRef2 = useRef<File | null>(null)  // stable ref for async callbacks
  const augParamsRef = useRef<Record<string, AugParams>>({})
  const MAX_CONCURRENT = 4

  // Keep refs in sync so async queue drains see latest values
  useEffect(() => { fileRef2.current = file }, [file])
  useEffect(() => { augParamsRef.current = augParams }, [augParams])

  // Clear thumbnails when file changes
  useEffect(() => {
    setThumbnails({})
    setPipelineResult(null)
    setSingleResult(null)
    setShowResult(false)
    previewQueue.current = []
    activeCount.current = 0
  }, [file])

  const filtered = phase === 'all' ? entries : entries.filter(e => e.phase === phase)

  const toggleEnabled = (name: string) => {
    setEnabled(prev => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }

  const toggleExpanded = (name: string) => {
    setExpanded(prev => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }

  // nocache nonces: per-card random string set when user clicks "Refresh preview"
  const nocacheRef = useRef<Record<string, string>>({})

  // Internal: run one preview immediately — uses stable refs for params/file
  const runPreview = (name: string) => {
    const currentFile = fileRef2.current
    if (!currentFile) return
    const currentParams = augParamsRef.current[name] ?? {}
    const nonce = nocacheRef.current[name] ?? ''
    delete nocacheRef.current[name]  // consume the nonce — only used once
    activeCount.current++
    setLoadingThumb(prev => new Set(prev).add(name))
    previewCatalogue(currentFile, name, JSON.stringify(currentParams), nonce)
      .then(result => setThumbnails(prev => ({ ...prev, [name]: result.augmented_b64 })))
      .catch(() => { /* silently ignore failed previews */ })
      .finally(() => {
        activeCount.current--
        setLoadingThumb(prev => { const s = new Set(prev); s.delete(name); return s })
        // drain queue — each queued item looks up its own params via ref
        if (previewQueue.current.length > 0) {
          const next = previewQueue.current.shift()!
          runPreview(next)
        }
      })
  }

  // Public: enqueue a preview (or fire immediately if slots free)
  const fetchPreview = (name: string, forceRefresh = false) => {
    if (!fileRef2.current) return
    if (loadingThumb.has(name)) return  // already running
    if (forceRefresh) {
      // Remove from queue if present so it re-runs with new nonce
      previewQueue.current = previewQueue.current.filter(n => n !== name)
      nocacheRef.current[name] = String(Date.now())  // bust backend cache
    } else {
      if (previewQueue.current.includes(name)) return  // already queued
    }
    if (activeCount.current < MAX_CONCURRENT) {
      runPreview(name)
    } else {
      setLoadingThumb(prev => new Set(prev).add(name))  // show "Loading…" while queued
      previewQueue.current.push(name)
    }
  }

  // Preview all entries (skip slow ones by default; they can be manually triggered)
  const previewAll = (includeSlowEntries = false) => {
    if (!fileRef2.current) return
    const toPreview = entries.filter(e => {
      if (thumbnails[e.name] || loadingThumb.has(e.name) || previewQueue.current.includes(e.name)) return false
      if (e.slow && !includeSlowEntries) return false
      return true
    })
    toPreview.forEach(e => fetchPreview(e.name))
  }

  // Auto-preview all fast entries when a file is first loaded / changed
  useEffect(() => {
    if (file && entries.length > 0) {
      previewAll(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [file, entries.length])

  // Progress stats
  const totalEntries = entries.length
  const loadedCount = Object.keys(thumbnails).length
  const inFlightCount = loadingThumb.size
  const fastEntries = entries.filter(e => !e.slow).length

  const handleApplySingle = async (name: string) => {
    if (!file) return
    setLoadingPipeline(true); setError(null)
    try {
      const params = augParams[name] ?? {}
      setSingleResult(await augmentCatalogue(file, name, JSON.stringify(params)))
      setPipelineResult(null)
      setShowResult(true)  // auto-expand on result
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoadingPipeline(false)
    }
  }

  const handleApplyPipeline = async () => {
    if (!file || enabled.size === 0) return
    setLoadingPipeline(true); setError(null)
    try {
      const ordered = entries.filter(e => enabled.has(e.name)).map(e => e.name)
      const result = await applyPipeline(file, ordered, augParams)
      setPipelineResult(result); setSingleResult(null)
      setShowResult(true)  // auto-expand on result
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoadingPipeline(false)
    }
  }

  const resultOriginal = pipelineResult?.original_b64 ?? singleResult?.original_b64
  const resultAugmented = pipelineResult?.augmented_b64 ?? singleResult?.augmented_b64
  const resultLabel = pipelineResult
    ? `Pipeline (${pipelineResult.applied.length} augs)`
    : singleResult ? singleResult.display_name : ''

  return (
    <>
      {/* File upload + pipeline controls */}
      <div style={card}>
        <ImageSourceSelector file={file} onFile={f => { setFile(f); setError(null) }} />
        {file && enabled.size > 0 && (
          <div style={{ marginTop: 12, display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
            <button
              style={loadingPipeline ? btnDisabled : btn}
              disabled={loadingPipeline}
              onClick={handleApplyPipeline}
            >
              {loadingPipeline ? 'Applying…' : `Apply Pipeline (${enabled.size} selected)`}
            </button>
            <button style={{ ...btnSm, background: '#e74c3c' }} onClick={() => setEnabled(new Set())}>
              Clear selection
            </button>
            <span style={{ fontSize: 13, color: '#555' }}>
              Selected: {entries.filter(e => enabled.has(e.name)).map(e => e.display_name).join(', ')}
            </span>
          </div>
        )}
        {error && <div style={{ marginTop: 12, color: '#c0392b', background: '#fdecea', padding: '8px 12px', borderRadius: 5, fontSize: 13 }}>{error}</div>}
      </div>

      {/* Collapsible Before / After result */}
      {file && (
        <div style={{ marginBottom: 16 }}>
          <button
            onClick={() => setShowResult(v => !v)}
            style={{
              display: 'flex', alignItems: 'center', gap: 8, width: '100%',
              padding: '10px 16px', borderRadius: 6, border: '1px solid #dde',
              background: showResult ? '#f0f4ff' : '#fafafa', cursor: 'pointer',
              fontSize: 13, fontWeight: 600, color: '#4f6ef7', textAlign: 'left',
            }}
          >
            <span style={{ fontSize: 16 }}>{showResult ? '▼' : '▶'}</span>
            {resultAugmented ? `Result — ${resultLabel}` : 'Result (click Apply or Apply Pipeline to generate)'}
          </button>

          {showResult && (
            <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', marginTop: 12 }}>
              <div style={{ ...card, flex: '1 1 280px', marginBottom: 0 }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#888', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Original</div>
                <LightboxImage
                  src={resultOriginal ? `data:image/png;base64,${resultOriginal}` : URL.createObjectURL(file)}
                  alt="Original" style={{ width: '100%', borderRadius: 4, border: '1px solid #eee' }} />
              </div>
              {resultAugmented && (
                <div style={{ ...card, flex: '1 1 280px', marginBottom: 0 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: '#888', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      {resultLabel}
                      {singleResult && (
                        <span style={{ marginLeft: 8, background: PHASE_BG[singleResult.phase], color: PHASE_COLORS[singleResult.phase], borderRadius: 4, padding: '1px 6px', fontSize: 10, fontWeight: 700 }}>
                          {singleResult.phase}
                        </span>
                      )}
                    </div>
                    <button style={btnSm} onClick={() => {
                      const a = document.createElement('a'); a.href = `data:image/png;base64,${resultAugmented}`
                      a.download = `${resultLabel.replace(/[^a-z0-9]/gi, '_')}.png`; a.click()
                    }}>Download</button>
                  </div>
                  <LightboxImage src={`data:image/png;base64,${resultAugmented}`} alt={resultLabel}
                    style={{ width: '100%', borderRadius: 4, border: '1px solid #eee' }} />
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── Batch Run — shown right after Result ───────────────────────────── */}
      {enabled.size > 0 && (
        <BatchSection
          augNames={entries.filter(e => enabled.has(e.name)).map(e => e.name)}
          augParams={augParams}
          pipelineLabel={entries.filter(e => enabled.has(e.name)).map(e => e.display_name).join(' → ')}
        />
      )}

      {/* Phase filter + Preview All */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        {(['all', 'ink', 'paper', 'post'] as const).map(p => (
          <button key={p} onClick={() => setPhase(p)} style={{
            padding: '5px 14px', borderRadius: 20, border: '1px solid #ddd', cursor: 'pointer', fontSize: 13,
            background: phase === p ? '#4f6ef7' : '#fafafa', color: phase === p ? '#fff' : '#444',
            fontWeight: phase === p ? 600 : 400,
          }}>{p === 'all' ? 'All phases' : p.charAt(0).toUpperCase() + p.slice(1)}</button>
        ))}
        {file && (
          <>
            <button onClick={() => previewAll(false)} style={{
              padding: '5px 14px', borderRadius: 20, border: '1px solid #2ecc71', cursor: 'pointer', fontSize: 13,
              background: '#f0fff4', color: '#27ae60', fontWeight: 600,
            }}>
              Preview fast ({entries.filter(e => !e.slow && !thumbnails[e.name] && !loadingThumb.has(e.name) && !previewQueue.current.includes(e.name)).length} remaining)
            </button>
            <button onClick={() => previewAll(true)} style={{
              padding: '5px 14px', borderRadius: 20, border: '1px solid #e67e22', cursor: 'pointer', fontSize: 13,
              background: '#fff8f0', color: '#e67e22', fontWeight: 600,
            }}>
              + Slow ones ({entries.filter(e => e.slow && !thumbnails[e.name] && !loadingThumb.has(e.name) && !previewQueue.current.includes(e.name)).length} remaining)
            </button>
          </>
        )}
        <span style={{ fontSize: 13, color: '#888' }}>
          {filtered.length} augmentation{filtered.length !== 1 ? 's' : ''}
          {enabled.size > 0 && ` · ${enabled.size} selected`}
        </span>
        {!file && (
          <span style={{ fontSize: 12, color: '#e67e22', marginLeft: 8 }}>
            Upload an image above to auto-load previews.
          </span>
        )}
      </div>

      {/* Progress bar — shown while loading previews */}
      {file && (loadedCount > 0 || inFlightCount > 0) && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#666', marginBottom: 4 }}>
            <span>Previews loaded: {loadedCount} / {fastEntries} fast{inFlightCount > 0 ? ` · ${inFlightCount} loading…` : ' ✓'}</span>
            <span style={{ color: '#aaa' }}>{totalEntries} total augmentations</span>
          </div>
          <div style={{ height: 4, background: '#eee', borderRadius: 2, overflow: 'hidden' }}>
            <div style={{
              height: '100%', borderRadius: 2,
              background: inFlightCount > 0 ? '#4f6ef7' : '#2ecc71',
              width: `${Math.round((loadedCount / Math.max(fastEntries, 1)) * 100)}%`,
              transition: 'width 0.3s ease, background 0.5s ease',
            }} />
          </div>
        </div>
      )}

      {/* Catalogue grid */}
      {loadingCatalogue ? (
        <div style={{ color: '#888', padding: '20px 0' }}>Loading catalogue…</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 10 }}>
          {filtered.map(entry => {
            const isEnabled = enabled.has(entry.name)
            const isExpanded = expanded.has(entry.name)
            const thumb = thumbnails[entry.name]
            const isLoadingThumb = loadingThumb.has(entry.name)
            const params = augParams[entry.name] ?? {}

            return (
              <div key={entry.name} style={{
                borderRadius: 8,
                border: `2px solid ${isEnabled ? '#4f6ef7' : '#e8e8e8'}`,
                background: isEnabled ? '#f0f4ff' : '#fff',
                transition: 'border-color 0.15s, background 0.15s',
                overflow: 'hidden',
              }}>
                {/* Card header */}
                <div style={{ padding: '12px 14px 8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 5 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <input type="checkbox" checked={isEnabled} onChange={() => toggleEnabled(entry.name)}
                        style={{ cursor: 'pointer', accentColor: '#4f6ef7', width: 15, height: 15 }} />
                      <span style={{ fontWeight: 600, fontSize: 13 }}>{entry.display_name}</span>
                    </div>
                    <span style={{
                      background: PHASE_BG[entry.phase], color: PHASE_COLORS[entry.phase],
                      borderRadius: 4, padding: '1px 6px', fontSize: 10, fontWeight: 700, whiteSpace: 'nowrap', marginLeft: 6,
                    }}>{entry.phase}</span>
                  </div>
                  <div style={{ fontSize: 12, color: '#666', lineHeight: 1.4, marginBottom: 5 }}>{entry.description}</div>
                  {entry.slow && (
                    <div style={{ fontSize: 11, color: '#e67e22', fontStyle: 'italic', marginBottom: 4 }}>⚠ slow</div>
                  )}

                  {/* Card action buttons */}
                  {file && (
                    <div style={{ display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap' }}>
                      <button style={{ ...btnSm, background: '#2ecc71' }}
                        onClick={() => handleApplySingle(entry.name)}
                        disabled={loadingPipeline}
                      >
                        Apply
                      </button>
                      <button
                        style={{ ...btnSm, background: thumb ? '#27ae60' : '#7f8c8d' }}
                        onClick={() => fetchPreview(entry.name, !!thumb)}
                        disabled={isLoadingThumb}
                      >
                        {isLoadingThumb ? 'Loading…' : thumb ? 'Re-roll preview' : 'Preview'}
                      </button>
                      <button style={{ ...btnSm, background: isExpanded ? '#e74c3c' : '#95a5a6' }}
                        onClick={() => toggleExpanded(entry.name)}>
                        {isExpanded ? 'Hide params' : 'Params'}
                      </button>
                    </div>
                  )}
                </div>

                {/* Per-card thumbnail preview */}
                {thumb && (
                  <div style={{ padding: '0 14px 10px' }}>
                    <LightboxImage src={`data:image/png;base64,${thumb}`} alt={`Preview: ${entry.display_name}`}
                      style={{ width: '100%', borderRadius: 4, border: '1px solid #ddd', display: 'block' }} />
                  </div>
                )}

                {/* Parameter controls */}
                {isExpanded && (
                  <div style={{ padding: '8px 14px 12px', borderTop: '1px solid #e8e8e8', background: '#fafafa' }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: '#555', marginBottom: 8 }}>Parameters</div>
                    <ParamControls
                      entry={entry}
                      params={params}
                      onChange={p => setAugParams(prev => ({ ...prev, [entry.name]: p }))}
                    />
                    {Object.keys(params).length > 0 && (
                      <button style={{ ...btnSm, background: '#e74c3c', marginTop: 4 }}
                        onClick={() => setAugParams(prev => {
                          const next = { ...prev }; delete next[entry.name]; return next
                        })}>
                        Reset to defaults
                      </button>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

    </>
  )
}

// ── Batch Run section (catalogue pipeline) ───────────────────────────────────

function BatchSection({
  augNames,
  augParams,
  pipelineLabel,
}: {
  augNames: string[]
  augParams: Record<string, Record<string, unknown>>
  pipelineLabel: string
}) {
  const [open, setOpen] = useState(false)
  const [batchFiles, setBatchFiles] = useState<File[]>([])
  const [mode, setMode] = useState<'per_template' | 'random_sample'>('per_template')
  const [copies, setCopies] = useState(3)
  const [total, setTotal] = useState(20)
  const [seed, setSeed] = useState(0)
  const [jobId, setJobId] = useState<string | null>(null)
  const [status, setStatus] = useState<CatalogueBatchStatus | null>(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  // Sample picker
  const [samples, setSamples] = useState<string[]>([])
  const [selectedSamples, setSelectedSamples] = useState<Set<string>>(new Set())
  const [loadingSamples, setLoadingSamples] = useState(false)

  const effTotal = mode === 'per_template' ? batchFiles.length * copies : total

  // Load sample list when section opens
  useEffect(() => {
    if (!open || samples.length > 0) return
    setLoadingSamples(true)
    listAugSamples().then(s => { setSamples(s); setLoadingSamples(false) }).catch(() => setLoadingSamples(false))
  }, [open])

  const stopPoll = () => { if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null } }

  useEffect(() => () => stopPoll(), [])

  const handleRun = async () => {
    const sampleFiles = await Promise.all([...selectedSamples].map(augSampleToFile))
    const allFiles = [...batchFiles, ...sampleFiles]
    if (!allFiles.length) return
    setRunning(true); setError(null); setStatus(null)
    try {
      const id = await startCatalogueBatch(allFiles, augNames, augParams, mode, copies, total, seed)
      setJobId(id)
      stopPoll()
      pollRef.current = setInterval(async () => {
        const s = await getCatalogueBatchStatus(id).catch(() => null)
        if (!s) return
        setStatus(s)
        if (s.status === 'done' || s.status === 'failed') {
          stopPoll()
          setRunning(false)
          if (s.status === 'failed') setError(s.error ?? 'Batch failed')
        }
      }, 1500)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      setRunning(false)
    }
  }

  return (
    <div style={{ marginTop: 20 }}>
      <button
        onClick={() => setOpen(v => !v)}
        style={{
          display: 'flex', alignItems: 'center', gap: 8, width: '100%',
          padding: '12px 16px', borderRadius: 6, border: '1px solid #dde',
          background: open ? '#f0f4ff' : '#fafafa', cursor: 'pointer',
          fontSize: 14, fontWeight: 600, color: '#4f6ef7', textAlign: 'left',
        }}
      >
        <span style={{ fontSize: 16 }}>{open ? '▼' : '▶'}</span>
        Batch Run with this pipeline ({augNames.length} augmentation{augNames.length !== 1 ? 's' : ''})
      </button>

      {open && (
        <div style={{ ...card, marginTop: 0, borderTop: 'none', borderRadius: '0 0 8px 8px' }}>
          <div style={{ fontSize: 12, color: '#888', marginBottom: 12 }}>
            Pipeline: <span style={{ fontWeight: 600, color: '#555' }}>{pipelineLabel}</span>
          </div>
          <p style={{ fontSize: 13, color: '#555', margin: '0 0 12px' }}>
            Upload N input templates. Apply the catalogue pipeline above to produce M augmented outputs.
          </p>

          {/* Multi-file upload */}
          <div style={{ marginBottom: 12 }}>
            <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 4 }}>
              Upload templates (images or PDFs)
            </label>
            <input
              type="file" multiple accept=".png,.jpg,.jpeg,.bmp,.tiff,.pdf"
              onChange={e => setBatchFiles(Array.from(e.target.files ?? []))}
              style={{ fontSize: 13 }}
            />
            {batchFiles.length > 0 && (
              <div style={{ fontSize: 12, color: '#555', marginTop: 4 }}>
                {batchFiles.length} file{batchFiles.length !== 1 ? 's' : ''} selected
              </div>
            )}
          </div>

          {/* Sample picker */}
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4 }}>
              Or use sample files
              {loadingSamples && <span style={{ fontWeight: 400, color: '#888', marginLeft: 8 }}>loading…</span>}
            </div>
            {samples.length === 0 && !loadingSamples && (
              <div style={{ fontSize: 12, color: '#aaa' }}>No samples available on this server.</div>
            )}
            {samples.length > 0 && (
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {samples.map(s => (
                  <label key={s} style={{ display: 'flex', alignItems: 'center', gap: 5, cursor: 'pointer', fontSize: 13,
                    padding: '4px 10px', borderRadius: 5, border: `1px solid ${selectedSamples.has(s) ? '#4f6ef7' : '#ddd'}`,
                    background: selectedSamples.has(s) ? '#f0f4ff' : '#fafafa' }}>
                    <input type="checkbox" checked={selectedSamples.has(s)}
                      onChange={() => setSelectedSamples(prev => {
                        const next = new Set(prev)
                        next.has(s) ? next.delete(s) : next.add(s)
                        return next
                      })} />
                    {s}
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* Total count summary */}
          {(batchFiles.length > 0 || selectedSamples.size > 0) && (
            <div style={{ fontSize: 12, color: '#555', marginBottom: 12 }}>
              Total input templates: {batchFiles.length + selectedSamples.size}
              {batchFiles.length > 0 && selectedSamples.size > 0 &&
                ` (${batchFiles.length} uploaded + ${selectedSamples.size} sample${selectedSamples.size !== 1 ? 's' : ''})`}
            </div>
          )}

          {/* Mode selector */}
          <div style={{ marginBottom: 12 }}>
            <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 6 }}>Output mode</label>
            <div style={{ display: 'flex', gap: 12 }}>
              {([
                ['per_template', 'N×M — copies per template'],
                ['random_sample', 'M-total — random sample from N inputs'],
              ] as const).map(([val, label]) => (
                <label key={val} style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', fontSize: 13 }}>
                  <input type="radio" value={val} checked={mode === val} onChange={() => setMode(val)} />
                  {label}
                </label>
              ))}
            </div>
          </div>

          {/* Copies / total */}
          {mode === 'per_template' ? (
            <div style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 12 }}>
              <label style={{ fontSize: 13, fontWeight: 600 }}>Copies per template (M)</label>
              <input type="number" min={1} max={200} value={copies}
                onChange={e => setCopies(Math.max(1, parseInt(e.target.value) || 1))}
                style={{ width: 80, fontSize: 13, padding: '4px 8px', borderRadius: 4, border: '1px solid #ccc' }} />
              <span style={{ fontSize: 12, color: '#888' }}>→ {effTotal} total outputs</span>
            </div>
          ) : (
            <div style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 12 }}>
              <label style={{ fontSize: 13, fontWeight: 600 }}>Total outputs (M)</label>
              <input type="number" min={1} max={1000} value={total}
                onChange={e => setTotal(Math.max(1, parseInt(e.target.value) || 1))}
                style={{ width: 100, fontSize: 13, padding: '4px 8px', borderRadius: 4, border: '1px solid #ccc' }} />
              {batchFiles.length > 0 && (
                <span style={{ fontSize: 12, color: '#888' }}>
                  sampled from {batchFiles.length} template{batchFiles.length !== 1 ? 's' : ''}
                </span>
              )}
            </div>
          )}

          {/* Seed */}
          <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 12 }}>
            <label style={{ fontSize: 13, fontWeight: 600 }}>Random seed</label>
            <input type="number" min={0} value={seed}
              onChange={e => setSeed(Math.max(0, parseInt(e.target.value) || 0))}
              style={{ width: 100, fontSize: 13, padding: '4px 8px', borderRadius: 4, border: '1px solid #ccc' }} />
            <span style={{ fontSize: 12, color: '#888' }}>0 = unseeded</span>
          </div>

          {effTotal > 50 && (
            <div style={{ marginBottom: 12, padding: '8px 12px', background: '#fff8e1', borderRadius: 5, fontSize: 12, color: '#8a6d00', border: '1px solid #ffe082' }}>
              ⚠ Generating {effTotal} images may take a while. Consider a smaller number first.
            </div>
          )}

          {/* Run button */}
          {(() => {
            const hasInputs = batchFiles.length > 0 || selectedSamples.size > 0
            return (
              <button
                style={running || !hasInputs ? btnDisabled : btn}
                disabled={running || !hasInputs}
                onClick={handleRun}
              >
                {running ? `Generating… (${Math.round((status?.progress ?? 0) * 100)}%)` : `Run Batch (${effTotal} outputs)`}
              </button>
            )
          })()}

          {/* Progress bar */}
          {running && (
            <div style={{ marginTop: 12 }}>
              <div style={{ height: 6, background: '#eee', borderRadius: 3, overflow: 'hidden' }}>
                <div style={{
                  height: '100%', background: '#4f6ef7', borderRadius: 3,
                  width: `${Math.round((status?.progress ?? 0) * 100)}%`,
                  transition: 'width 0.4s ease',
                }} />
              </div>
              <div style={{ fontSize: 12, color: '#888', marginTop: 4 }}>
                {status ? `${Math.round(status.progress * 100)}% — ${status.status}` : 'Starting…'}
              </div>
            </div>
          )}

          {error && (
            <div style={{ marginTop: 12, color: '#c0392b', background: '#fdecea', padding: '8px 12px', borderRadius: 5, fontSize: 13 }}>
              {error}
            </div>
          )}

          {/* Results */}
          {status?.status === 'done' && (
            <div style={{ marginTop: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                <span style={{ fontSize: 14, fontWeight: 600, color: '#27ae60' }}>
                  ✓ Generated {status.n_outputs} output{(status.n_outputs ?? 0) !== 1 ? 's' : ''}
                </span>
                <a
                  href={catalogueBatchDownloadUrl(jobId!)}
                  download
                  style={{ ...btn, textDecoration: 'none', display: 'inline-block', fontSize: 13 }}
                >
                  ⬇ Download all as ZIP
                </a>
              </div>

              {/* Thumbnail grid (up to 8) */}
              {status.thumbnails_b64.length > 0 && (
                <>
                  <div style={{ fontSize: 12, color: '#888', marginBottom: 8 }}>
                    Preview (first {status.thumbnails_b64.length} of {status.n_outputs})
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 8 }}>
                    {status.thumbnails_b64.map((b64, i) => (
                      <LightboxImage
                        key={i}
                        src={`data:image/png;base64,${b64}`}
                        alt={`Batch output ${i + 1}`}
                        style={{ width: '100%', borderRadius: 4, border: '1px solid #eee', display: 'block' }}
                      />
                    ))}
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function AugmentationLab() {
  const [tab, setTab] = useState<'preset' | 'catalogue'>('preset')

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: '24px 24px' }}>
      <h2 style={{ margin: '0 0 4px', fontSize: 22 }}>Augmentation Lab</h2>
      <p style={{ color: '#666', margin: '0 0 20px', fontSize: 14 }}>
        Apply document degradation presets or choose from individual Augraphy augmentations — previews auto-load on upload, with parameter tuning and multi-augmentation pipelines.
      </p>

      {/* Tab switcher */}
      <div style={{ display: 'flex', gap: 0, marginBottom: 20, borderBottom: '2px solid #e8e8e8' }}>
        {([['preset', 'Presets'], ['catalogue', 'Full Catalogue']] as const).map(([id, label]) => (
          <button key={id} onClick={() => setTab(id)} style={{
            padding: '8px 22px', border: 'none', cursor: 'pointer', fontSize: 14,
            fontWeight: tab === id ? 700 : 400,
            borderBottom: `3px solid ${tab === id ? '#4f6ef7' : 'transparent'}`,
            background: 'none', color: tab === id ? '#4f6ef7' : '#555',
            marginBottom: -2,
          }}>{label}</button>
        ))}
      </div>

      {tab === 'preset' ? <PresetTab /> : <CatalogueTab />}
    </div>
  )
}
