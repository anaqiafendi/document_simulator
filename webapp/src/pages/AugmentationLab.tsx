import { useEffect, useRef, useState } from 'react'
import { augmentImage, listPresets, listCatalogue, augmentCatalogue } from '../api/client'
import type { AugmentResult, CatalogueEntry, CatalogueAugmentResult } from '../types'

// ── Styles ────────────────────────────────────────────────────────────────────

const card: React.CSSProperties = {
  background: '#fff', borderRadius: 8, border: '1px solid #e0e0e0',
  padding: '16px 20px', marginBottom: 16,
}

const btn: React.CSSProperties = {
  padding: '8px 20px', borderRadius: 6, border: 'none', cursor: 'pointer',
  fontSize: 14, fontWeight: 600, background: '#4f6ef7', color: '#fff',
}

const btnDisabled: React.CSSProperties = { ...btn, background: '#aaa', cursor: 'not-allowed' }

const PHASE_COLORS: Record<string, string> = {
  ink: '#6c3483',
  paper: '#1a6648',
  post: '#1a3a6b',
}

const PHASE_BG: Record<string, string> = {
  ink: '#f5eef8',
  paper: '#eafaf1',
  post: '#eaf0fb',
}

// ── Preset tab ────────────────────────────────────────────────────────────────

function PresetTab() {
  const [presets, setPresets] = useState<string[]>([])
  const [preset, setPreset] = useState('medium')
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<AugmentResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    listPresets().then(setPresets).catch(() => setPresets(['light', 'medium', 'heavy', 'default']))
  }, [])

  const handleAugment = async () => {
    if (!file) return
    setLoading(true); setError(null)
    try {
      setResult(await augmentImage(file, preset))
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div style={card}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div>
            <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 4 }}>Document image</label>
            <input ref={fileRef} type="file" accept=".png,.jpg,.jpeg,.bmp,.tiff,.pdf"
              onChange={e => { setFile(e.target.files?.[0] ?? null); setResult(null); setError(null) }}
              style={{ fontSize: 13 }} />
          </div>
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

      {(file || result) && (
        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
          <div style={{ ...card, flex: '1 1 300px' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#888', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Original</div>
            <img src={result ? `data:image/png;base64,${result.original_b64}` : (file ? URL.createObjectURL(file) : '')}
              alt="Original" style={{ width: '100%', borderRadius: 4, border: '1px solid #eee' }} />
          </div>
          {result && (
            <div style={{ ...card, flex: '1 1 300px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#888', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Augmented — {result.metadata.preset}
                </div>
                <button style={{ ...btn, padding: '4px 12px', fontSize: 12 }} onClick={() => {
                  const a = document.createElement('a'); a.href = `data:image/png;base64,${result.augmented_b64}`
                  a.download = `augmented_${preset}.png`; a.click()
                }}>Download PNG</button>
              </div>
              <img src={`data:image/png;base64,${result.augmented_b64}`} alt="Augmented"
                style={{ width: '100%', borderRadius: 4, border: '1px solid #eee' }} />
            </div>
          )}
        </div>
      )}
      {!file && !result && (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#bbb', fontSize: 14 }}>Upload a document image to begin.</div>
      )}
    </>
  )
}

// ── Catalogue tab ─────────────────────────────────────────────────────────────

function CatalogueTab() {
  const [entries, setEntries] = useState<CatalogueEntry[]>([])
  const [phase, setPhase] = useState<'all' | 'ink' | 'paper' | 'post'>('all')
  const [selected, setSelected] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<CatalogueAugmentResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loadingCatalogue, setLoadingCatalogue] = useState(true)

  useEffect(() => {
    listCatalogue()
      .then(setEntries)
      .catch(() => setError('Failed to load catalogue'))
      .finally(() => setLoadingCatalogue(false))
  }, [])

  const filtered = phase === 'all' ? entries : entries.filter(e => e.phase === phase)

  const handleApply = async () => {
    if (!file || !selected) return
    setLoading(true); setError(null)
    try {
      setResult(await augmentCatalogue(file, selected))
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* File upload + apply bar */}
      <div style={card}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div>
            <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 4 }}>Document image</label>
            <input type="file" accept=".png,.jpg,.jpeg,.bmp,.tiff,.pdf"
              onChange={e => { setFile(e.target.files?.[0] ?? null); setResult(null); setError(null) }}
              style={{ fontSize: 13 }} />
          </div>
          <div style={{ fontSize: 13, color: '#555', alignSelf: 'center' }}>
            {selected ? <>Selected: <strong>{entries.find(e => e.name === selected)?.display_name ?? selected}</strong></> : 'Select an augmentation below'}
          </div>
          <button style={loading || !file || !selected ? btnDisabled : btn}
            disabled={loading || !file || !selected} onClick={handleApply}>
            {loading ? 'Applying…' : 'Apply'}
          </button>
        </div>
        {error && <div style={{ marginTop: 12, color: '#c0392b', background: '#fdecea', padding: '8px 12px', borderRadius: 5, fontSize: 13 }}>{error}</div>}
      </div>

      {/* Before / After */}
      {(file || result) && (
        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', marginBottom: 16 }}>
          <div style={{ ...card, flex: '1 1 280px', marginBottom: 0 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#888', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Original</div>
            <img src={result ? `data:image/png;base64,${result.original_b64}` : (file ? URL.createObjectURL(file) : '')}
              alt="Original" style={{ width: '100%', borderRadius: 4, border: '1px solid #eee' }} />
          </div>
          {result && (
            <div style={{ ...card, flex: '1 1 280px', marginBottom: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#888', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  {result.display_name}
                  <span style={{ marginLeft: 8, background: PHASE_BG[result.phase], color: PHASE_COLORS[result.phase], borderRadius: 4, padding: '1px 6px', fontSize: 10, fontWeight: 700 }}>
                    {result.phase}
                  </span>
                </div>
                <button style={{ ...btn, padding: '4px 12px', fontSize: 12 }} onClick={() => {
                  const a = document.createElement('a'); a.href = `data:image/png;base64,${result.augmented_b64}`
                  a.download = `${result.aug_name}.png`; a.click()
                }}>Download</button>
              </div>
              <img src={`data:image/png;base64,${result.augmented_b64}`} alt="Augmented"
                style={{ width: '100%', borderRadius: 4, border: '1px solid #eee' }} />
            </div>
          )}
        </div>
      )}

      {/* Phase filter */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        {(['all', 'ink', 'paper', 'post'] as const).map(p => (
          <button key={p} onClick={() => setPhase(p)} style={{
            padding: '5px 14px', borderRadius: 20, border: '1px solid #ddd', cursor: 'pointer', fontSize: 13,
            background: phase === p ? '#4f6ef7' : '#fafafa', color: phase === p ? '#fff' : '#444',
            fontWeight: phase === p ? 600 : 400,
          }}>{p === 'all' ? 'All phases' : p.charAt(0).toUpperCase() + p.slice(1)}</button>
        ))}
        <span style={{ marginLeft: 8, fontSize: 13, color: '#888', alignSelf: 'center' }}>
          {filtered.length} augmentation{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Catalogue grid */}
      {loadingCatalogue ? (
        <div style={{ color: '#888', padding: '20px 0' }}>Loading catalogue…</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 10 }}>
          {filtered.map(entry => (
            <div key={entry.name} onClick={() => setSelected(s => s === entry.name ? null : entry.name)}
              style={{
                borderRadius: 8, border: `2px solid ${selected === entry.name ? '#4f6ef7' : '#e8e8e8'}`,
                padding: '12px 14px', cursor: 'pointer', background: selected === entry.name ? '#f0f4ff' : '#fff',
                transition: 'border-color 0.15s, background 0.15s',
              }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 5 }}>
                <div style={{ fontWeight: 600, fontSize: 13 }}>{entry.display_name}</div>
                <span style={{
                  background: PHASE_BG[entry.phase], color: PHASE_COLORS[entry.phase],
                  borderRadius: 4, padding: '1px 6px', fontSize: 10, fontWeight: 700, whiteSpace: 'nowrap', marginLeft: 6,
                }}>{entry.phase}</span>
              </div>
              <div style={{ fontSize: 12, color: '#666', lineHeight: 1.4 }}>{entry.description}</div>
              {entry.slow && (
                <div style={{ marginTop: 6, fontSize: 11, color: '#e67e22', fontStyle: 'italic' }}>⚠ slow</div>
              )}
            </div>
          ))}
        </div>
      )}
    </>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function AugmentationLab() {
  const [tab, setTab] = useState<'preset' | 'catalogue'>('preset')

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px 24px' }}>
      <h2 style={{ margin: '0 0 4px', fontSize: 22 }}>Augmentation Lab</h2>
      <p style={{ color: '#666', margin: '0 0 20px', fontSize: 14 }}>
        Apply document degradation presets or choose from 51 individual Augraphy augmentations.
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
