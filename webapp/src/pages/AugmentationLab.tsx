import { useEffect, useRef, useState } from 'react'
import {
  augmentImage, listPresets,
  listCatalogue, augmentCatalogue, previewCatalogue, applyPipeline,
  listAugSamples, loadAugSample,
} from '../api/client'
import type { AugmentResult, CatalogueEntry, CatalogueAugmentResult, PipelineResult } from '../types'

// ── Shared: load a sample template (augmentation_lab dir) and convert to File ─

async function augSampleToFile(filename: string): Promise<File> {
  const info = await loadAugSample(filename, 250, 0)  // 250 DPI for sharp augmentation input
  const blob = await fetch(`data:image/png;base64,${info.image_b64}`).then(r => r.blob())
  return new File([blob], filename.replace(/\.pdf$/i, '') + '.png', { type: 'image/png' })
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
  const fmt = (v: number) => step < 1 ? v.toFixed(2) : String(v)
  const pct = (v: number) => ((v - rangeMin) / (rangeMax - rangeMin)) * 100

  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: '#555' }}>{label}</span>
        <span style={{ fontSize: 12, color: '#4f6ef7', fontWeight: 600 }}>{fmt(lo)} – {fmt(hi)}</span>
      </div>
      {/* Track container */}
      <div style={{ position: 'relative', height: 28 }}>
        {/* Background track */}
        <div style={{
          position: 'absolute', top: '50%', left: 0, right: 0,
          height: 4, background: '#dde', borderRadius: 2, transform: 'translateY(-50%)',
        }} />
        {/* Filled segment */}
        <div style={{
          position: 'absolute', top: '50%',
          left: `${pct(lo)}%`, width: `${pct(hi) - pct(lo)}%`,
          height: 4, background: '#4f6ef7', borderRadius: 2, transform: 'translateY(-50%)',
        }} />
        {/* Min thumb (visual) */}
        <div style={{
          position: 'absolute', top: '50%', left: `${pct(lo)}%`,
          width: 16, height: 16, borderRadius: '50%',
          background: '#4f6ef7', border: '2px solid #fff',
          boxShadow: '0 1px 4px rgba(0,0,0,0.25)',
          transform: 'translate(-50%, -50%)', pointerEvents: 'none',
        }} />
        {/* Max thumb (visual) */}
        <div style={{
          position: 'absolute', top: '50%', left: `${pct(hi)}%`,
          width: 16, height: 16, borderRadius: '50%',
          background: '#4f6ef7', border: '2px solid #fff',
          boxShadow: '0 1px 4px rgba(0,0,0,0.25)',
          transform: 'translate(-50%, -50%)', pointerEvents: 'none',
        }} />
        {/* Invisible inputs for interaction */}
        <input type="range" min={rangeMin} max={rangeMax} step={step} value={lo}
          onChange={e => onChange([Math.min(parseFloat(e.target.value), hi - step), hi])}
          style={{
            position: 'absolute', top: 0, left: 0, width: '100%', height: '100%',
            opacity: 0, cursor: 'pointer', margin: 0,
            // Lo handle on top only when near max, so user can always grab it
            zIndex: lo > (rangeMin + rangeMax) / 2 ? 2 : 1,
          }}
        />
        <input type="range" min={rangeMin} max={rangeMax} step={step} value={hi}
          onChange={e => onChange([lo, Math.max(parseFloat(e.target.value), lo + step)])}
          style={{
            position: 'absolute', top: 0, left: 0, width: '100%', height: '100%',
            opacity: 0, cursor: 'pointer', margin: 0,
            zIndex: lo > (rangeMin + rangeMax) / 2 ? 1 : 2,
          }}
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
    const arr = get(k, dp[k]) as [number, number]
    return (
      <DualRangeSlider
        label={label} rangeMin={min} rangeMax={max} step={step}
        value={[Number(arr[0]), Number(arr[1])]}
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
    return <RangeRow k="fold_count" label="Fold count" min={1} max={6} step={1} />
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
        const sliderMax = Math.max(arr[1] * 2, 1)
        return (
          <RangeRow key={k} k={k} label={k.replace(/_/g, ' ')}
            min={0} max={sliderMax} step={isFloat ? 0.05 : 1} />
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

  // Clear thumbnails when file changes
  useEffect(() => { setThumbnails({}); setPipelineResult(null); setSingleResult(null); setShowResult(false) }, [file])

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

  const fetchPreview = async (name: string) => {
    if (!file || loadingThumb.has(name)) return
    setLoadingThumb(prev => new Set(prev).add(name))
    try {
      const params = augParams[name] ?? {}
      const result = await previewCatalogue(file, name, JSON.stringify(params))
      setThumbnails(prev => ({ ...prev, [name]: result.augmented_b64 }))
    } catch {
      // ignore — card just won't show a preview
    } finally {
      setLoadingThumb(prev => { const s = new Set(prev); s.delete(name); return s })
    }
  }

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

      {/* Phase filter */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        {(['all', 'ink', 'paper', 'post'] as const).map(p => (
          <button key={p} onClick={() => setPhase(p)} style={{
            padding: '5px 14px', borderRadius: 20, border: '1px solid #ddd', cursor: 'pointer', fontSize: 13,
            background: phase === p ? '#4f6ef7' : '#fafafa', color: phase === p ? '#fff' : '#444',
            fontWeight: phase === p ? 600 : 400,
          }}>{p === 'all' ? 'All phases' : p.charAt(0).toUpperCase() + p.slice(1)}</button>
        ))}
        <span style={{ fontSize: 13, color: '#888' }}>
          {filtered.length} augmentation{filtered.length !== 1 ? 's' : ''}
          {enabled.size > 0 && ` · ${enabled.size} selected`}
        </span>
        {!file && (
          <span style={{ fontSize: 12, color: '#e67e22', marginLeft: 8 }}>
            Upload an image above to enable previews and apply augmentations.
          </span>
        )}
      </div>

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
                        onClick={() => fetchPreview(entry.name)}
                        disabled={isLoadingThumb}
                      >
                        {isLoadingThumb ? 'Loading…' : thumb ? 'Refresh preview' : 'Preview'}
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

// ── Main page ─────────────────────────────────────────────────────────────────

export default function AugmentationLab() {
  const [tab, setTab] = useState<'preset' | 'catalogue'>('preset')

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: '24px 24px' }}>
      <h2 style={{ margin: '0 0 4px', fontSize: 22 }}>Augmentation Lab</h2>
      <p style={{ color: '#666', margin: '0 0 20px', fontSize: 14 }}>
        Apply document degradation presets or choose from 51 individual Augraphy augmentations — with per-card previews, parameter tuning, and multi-augmentation pipelines.
      </p>

      {/* Tab switcher */}
      <div style={{ display: 'flex', gap: 0, marginBottom: 20, borderBottom: '2px solid #e8e8e8' }}>
        {([['preset', 'Presets'], ['catalogue', 'Full Catalogue (51)']] as const).map(([id, label]) => (
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
