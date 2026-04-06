import { useEffect, useState } from 'react'
import type { PreviewSample, SynthesisConfig } from '../types'

interface Props {
  previews: PreviewSample[]
  loading: boolean
  config: SynthesisConfig
  onPreview: () => void
  onReroll: (idx: number) => void
}

export default function PreviewGallery({ previews, loading, onPreview, onReroll }: Props) {
  const [lightboxSrc, setLightboxSrc] = useState<string | null>(null)

  // Bug 3: close lightbox on Escape key
  useEffect(() => {
    if (!lightboxSrc) return
    const handle = (e: KeyboardEvent) => { if (e.key === 'Escape') setLightboxSrc(null) }
    window.addEventListener('keydown', handle)
    return () => window.removeEventListener('keydown', handle)
  }, [lightboxSrc])

  return (
    <div>
      <button onClick={onPreview} disabled={loading} style={{ marginBottom: 12 }}>
        {loading ? 'Loading...' : 'Preview (3 samples)'}
      </button>
      {previews.length > 0 && (
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          {previews.map((sample, i) => (
            <div key={sample.seed} style={{ textAlign: 'center' }}>
              <img
                src={`data:image/png;base64,${sample.image_b64}`}
                alt={`Sample seed=${sample.seed}`}
                title="Click to expand"
                style={{ width: 250, border: '1px solid #ccc', display: 'block', cursor: 'zoom-in' }}
                onClick={() => setLightboxSrc(`data:image/png;base64,${sample.image_b64}`)}
              />
              <div style={{ fontSize: 11, color: '#999', marginTop: 2 }}>seed={sample.seed}</div>
              <button onClick={() => onReroll(i)} style={{ marginTop: 4, fontSize: 12 }}>
                &#8635; Re-roll
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Bug 3: Lightbox overlay */}
      {lightboxSrc && (
        <div
          onClick={() => setLightboxSrc(null)}
          style={{
            position: 'fixed', inset: 0,
            background: 'rgba(0,0,0,0.8)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            zIndex: 9999,
          }}
        >
          {/* Close button */}
          <button
            onClick={e => { e.stopPropagation(); setLightboxSrc(null) }}
            style={{
              position: 'fixed', top: 16, right: 20,
              background: 'rgba(255,255,255,0.15)', border: 'none',
              color: '#fff', fontSize: 28, fontWeight: 700,
              cursor: 'pointer', lineHeight: 1, padding: '2px 8px', borderRadius: 4,
            }}
            aria-label="Close"
          >
            &times;
          </button>
          {/* Image — stop propagation so clicking the image itself doesn't close */}
          <img
            src={lightboxSrc}
            alt="Full-size preview"
            onClick={e => e.stopPropagation()}
            style={{ maxWidth: '95vw', maxHeight: '95vh', objectFit: 'contain', display: 'block' }}
          />
        </div>
      )}
    </div>
  )
}
