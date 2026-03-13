import { useEffect, useRef, useState } from 'react'
import { augmentImage, listPresets } from '../api/client'
import type { AugmentResult } from '../types'

const card: React.CSSProperties = {
  background: '#fff', borderRadius: 8, border: '1px solid #e0e0e0',
  padding: '16px 20px', marginBottom: 16,
}

const btn: React.CSSProperties = {
  padding: '8px 20px', borderRadius: 6, border: 'none', cursor: 'pointer',
  fontSize: 14, fontWeight: 600, background: '#4f6ef7', color: '#fff',
}

const btnDisabled: React.CSSProperties = { ...btn, background: '#aaa', cursor: 'not-allowed' }

export default function AugmentationLab() {
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
    setLoading(true)
    setError(null)
    try {
      const res = await augmentImage(file, preset)
      setResult(res)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    if (!result) return
    const link = document.createElement('a')
    link.href = `data:image/png;base64,${result.augmented_b64}`
    link.download = `augmented_${preset}.png`
    link.click()
  }

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '24px 24px' }}>
      <h2 style={{ margin: '0 0 4px', fontSize: 22 }}>Augmentation Lab</h2>
      <p style={{ color: '#666', margin: '0 0 20px', fontSize: 14 }}>
        Upload a document image, choose a degradation preset, and get an augmented copy.
      </p>

      <div style={card}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          {/* File upload */}
          <div>
            <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 4 }}>
              Document image
            </label>
            <input
              ref={fileRef}
              type="file"
              accept=".png,.jpg,.jpeg,.bmp,.tiff,.pdf"
              onChange={e => {
                setFile(e.target.files?.[0] ?? null)
                setResult(null)
                setError(null)
              }}
              style={{ fontSize: 13 }}
            />
          </div>

          {/* Preset selector */}
          <div>
            <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 4 }}>
              Preset
            </label>
            <select
              value={preset}
              onChange={e => setPreset(e.target.value)}
              style={{ fontSize: 13, padding: '6px 10px', borderRadius: 5, border: '1px solid #ccc' }}
            >
              {(presets.length > 0 ? presets : ['light', 'medium', 'heavy', 'default']).map(p => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>

          {/* Run button */}
          <button
            style={loading || !file ? btnDisabled : btn}
            disabled={loading || !file}
            onClick={handleAugment}
          >
            {loading ? 'Augmenting…' : 'Augment'}
          </button>
        </div>

        {error && (
          <div style={{ marginTop: 12, color: '#c0392b', background: '#fdecea', padding: '8px 12px', borderRadius: 5, fontSize: 13 }}>
            {error}
          </div>
        )}
      </div>

      {/* Before / After */}
      {(file || result) && (
        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
          {/* Original */}
          <div style={{ ...card, flex: '1 1 300px' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#888', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Original
            </div>
            {file && !result && (
              <img
                src={URL.createObjectURL(file)}
                alt="Original"
                style={{ width: '100%', borderRadius: 4, border: '1px solid #eee' }}
              />
            )}
            {result && (
              <img
                src={`data:image/png;base64,${result.original_b64}`}
                alt="Original"
                style={{ width: '100%', borderRadius: 4, border: '1px solid #eee' }}
              />
            )}
          </div>

          {/* Augmented */}
          {result && (
            <div style={{ ...card, flex: '1 1 300px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#888', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Augmented — {result.metadata.preset}
                </div>
                <button
                  style={{ ...btn, padding: '4px 12px', fontSize: 12 }}
                  onClick={handleDownload}
                >
                  Download PNG
                </button>
              </div>
              <img
                src={`data:image/png;base64,${result.augmented_b64}`}
                alt="Augmented"
                style={{ width: '100%', borderRadius: 4, border: '1px solid #eee' }}
              />
              <div style={{ marginTop: 10, fontSize: 12, color: '#666', display: 'flex', gap: 16 }}>
                <span>Width: {result.metadata.width}px</span>
                <span>Height: {result.metadata.height}px</span>
                <span>Preset: <strong>{result.metadata.preset}</strong></span>
              </div>
            </div>
          )}
        </div>
      )}

      {!file && !result && (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#bbb', fontSize: 14 }}>
          Upload a document image to begin.
        </div>
      )}
    </div>
  )
}
