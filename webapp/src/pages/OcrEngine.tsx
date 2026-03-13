import { useState } from 'react'
import { recognizeOcr } from '../api/client'
import type { OcrResult } from '../types'

const card: React.CSSProperties = {
  background: '#fff', borderRadius: 8, border: '1px solid #e0e0e0',
  padding: '16px 20px', marginBottom: 16,
}

const btn: React.CSSProperties = {
  padding: '8px 20px', borderRadius: 6, border: 'none', cursor: 'pointer',
  fontSize: 14, fontWeight: 600, background: '#4f6ef7', color: '#fff',
}

const btnDisabled: React.CSSProperties = { ...btn, background: '#aaa', cursor: 'not-allowed' }

const LANGS = ['en', 'ch', 'fr', 'de', 'es', 'ja', 'ko']

export default function OcrEngine() {
  const [file, setFile] = useState<File | null>(null)
  const [lang, setLang] = useState('en')
  const [useGpu, setUseGpu] = useState(false)
  const [result, setResult] = useState<OcrResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleRun = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const res = await recognizeOcr(file, lang, useGpu)
      setResult(res)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadText = () => {
    if (!result) return
    const blob = new Blob([result.text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'extracted_text.txt'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '24px 24px' }}>
      <h2 style={{ margin: '0 0 4px', fontSize: 22 }}>OCR Engine</h2>
      <p style={{ color: '#666', margin: '0 0 20px', fontSize: 14 }}>
        Upload a document image or PDF, run OCR, and inspect bounding boxes and extracted text.
      </p>

      <div style={card}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div>
            <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 4 }}>
              Document image / PDF
            </label>
            <input
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
          <div>
            <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 4 }}>
              Language
            </label>
            <select
              value={lang}
              onChange={e => setLang(e.target.value)}
              style={{ fontSize: 13, padding: '6px 10px', borderRadius: 5, border: '1px solid #ccc' }}
            >
              {LANGS.map(l => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={useGpu}
              onChange={e => setUseGpu(e.target.checked)}
            />
            Use GPU
          </label>
          <button
            style={loading || !file ? btnDisabled : btn}
            disabled={loading || !file}
            onClick={handleRun}
          >
            {loading ? 'Running OCR…' : 'Run OCR'}
          </button>
        </div>

        {error && (
          <div style={{ marginTop: 12, color: '#c0392b', background: '#fdecea', padding: '8px 12px', borderRadius: 5, fontSize: 13 }}>
            {error}
          </div>
        )}
      </div>

      {/* Metrics row */}
      {result && (
        <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
          {[
            { label: 'Mean Confidence', value: result.mean_confidence.toFixed(3) },
            { label: 'Regions Detected', value: String(result.n_regions) },
          ].map(({ label, value }) => (
            <div key={label} style={{ ...card, flex: '0 0 auto', textAlign: 'center', minWidth: 120 }}>
              <div style={{ fontSize: 11, color: '#888', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#333', marginTop: 4 }}>{value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Side-by-side: annotated image + text */}
      {result && (
        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
          <div style={{ ...card, flex: '1 1 300px' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#888', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Detected Text Regions
            </div>
            <img
              src={`data:image/png;base64,${result.annotated_b64}`}
              alt="Annotated document"
              style={{ width: '100%', borderRadius: 4, border: '1px solid #eee' }}
            />
          </div>

          <div style={{ ...card, flex: '1 1 300px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#888', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Extracted Text
              </div>
              <button style={{ ...btn, padding: '4px 12px', fontSize: 12 }} onClick={handleDownloadText}>
                Download .txt
              </button>
            </div>
            <textarea
              readOnly
              value={result.text}
              style={{
                width: '100%', minHeight: 160, fontSize: 13, fontFamily: 'monospace',
                border: '1px solid #e0e0e0', borderRadius: 5, padding: 8,
                resize: 'vertical', boxSizing: 'border-box',
              }}
            />

            {/* Region table */}
            <div style={{ fontSize: 12, fontWeight: 700, color: '#888', marginTop: 16, marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Region Details
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ background: '#f5f5f5' }}>
                    {['#', 'Text', 'Confidence', 'Top-left (x, y)'].map(h => (
                      <th key={h} style={{ padding: '6px 10px', textAlign: 'left', borderBottom: '1px solid #e0e0e0', fontWeight: 600 }}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.boxes.map((box, i) => {
                    const textLines = result.text.split('\n')
                    return (
                      <tr key={i} style={{ borderBottom: '1px solid #f0f0f0' }}>
                        <td style={{ padding: '5px 10px', color: '#888' }}>{i + 1}</td>
                        <td style={{ padding: '5px 10px', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {textLines[i] ?? ''}
                        </td>
                        <td style={{ padding: '5px 10px' }}>
                          {result.scores[i] !== undefined ? result.scores[i].toFixed(4) : '—'}
                        </td>
                        <td style={{ padding: '5px 10px', fontFamily: 'monospace', fontSize: 11, color: '#666' }}>
                          ({Math.round(box[0]?.[0] ?? 0)}, {Math.round(box[0]?.[1] ?? 0)})
                        </td>
                      </tr>
                    )
                  })}
                  {result.boxes.length === 0 && (
                    <tr>
                      <td colSpan={4} style={{ padding: '12px 10px', color: '#bbb', textAlign: 'center' }}>
                        No regions detected.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {!file && !result && (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#bbb', fontSize: 14 }}>
          Upload a document image to begin.
        </div>
      )}
      {file && !result && !loading && (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#999', fontSize: 14 }}>
          Click <strong>Run OCR</strong> to extract text from the uploaded document.
        </div>
      )}
    </div>
  )
}
