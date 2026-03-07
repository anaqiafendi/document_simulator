import type { PreviewSample, SynthesisConfig } from '../types'

interface Props {
  previews: PreviewSample[]
  loading: boolean
  config: SynthesisConfig
  onPreview: () => void
  onReroll: (idx: number) => void
}

export default function PreviewGallery({ previews, loading, onPreview, onReroll }: Props) {
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
                style={{ width: 250, border: '1px solid #ccc', display: 'block' }}
              />
              <div style={{ fontSize: 11, color: '#999', marginTop: 2 }}>seed={sample.seed}</div>
              <button onClick={() => onReroll(i)} style={{ marginTop: 4, fontSize: 12 }}>
                &#8635; Re-roll
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
