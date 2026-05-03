import type { CSSProperties } from 'react'
import type { HDRIInfo } from '../../types'

interface HDRIPickerProps {
  hdris: HDRIInfo[]
  selectedId: string | null
  onSelect: (id: string) => void
  loading?: boolean
  error?: string | null
  onRetry?: () => void
  /** When false, the picker visually fades to communicate that the picked
   *  HDRI won't currently affect the render (i.e. render_3d is off). */
  enabled?: boolean
}

const wrap: CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: 6,
}

const grid: CSSProperties = {
  display: 'flex',
  gap: 8,
  flexWrap: 'wrap',
  alignItems: 'flex-start',
}

const thumbBase: CSSProperties = {
  position: 'relative',
  width: 78,
  height: 78,
  borderRadius: 6,
  border: '2px solid #d8d8d8',
  background: '#fafafa',
  cursor: 'pointer',
  overflow: 'hidden',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: 0,
  transition: 'border-color 0.15s, box-shadow 0.15s, transform 0.1s',
}

const thumbSelected: CSSProperties = {
  borderColor: '#4f6ef7',
  boxShadow: '0 0 0 3px rgba(79,110,247,0.18)',
}

const captionStyle: CSSProperties = {
  fontSize: 10,
  color: '#666',
  textAlign: 'center',
  marginTop: 3,
  maxWidth: 78,
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
}

const checkBadge: CSSProperties = {
  position: 'absolute',
  top: 3,
  right: 3,
  width: 18,
  height: 18,
  borderRadius: '50%',
  background: '#4f6ef7',
  color: '#fff',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: 11,
  fontWeight: 700,
  boxShadow: '0 1px 2px rgba(0,0,0,0.18)',
  pointerEvents: 'none',
}

const emptyBox: CSSProperties = {
  border: '1px dashed #d6d6d6',
  borderRadius: 6,
  padding: '10px 14px',
  fontSize: 12,
  color: '#888',
  background: '#fafafa',
  display: 'flex',
  alignItems: 'center',
  gap: 10,
}

const retryBtn: CSSProperties = {
  padding: '4px 10px',
  borderRadius: 4,
  border: '1px solid #ccc',
  background: '#fff',
  cursor: 'pointer',
  fontSize: 12,
  color: '#333',
}

export default function HDRIPicker({
  hdris,
  selectedId,
  onSelect,
  loading = false,
  error = null,
  onRetry,
  enabled = true,
}: HDRIPickerProps) {
  if (loading) {
    return (
      <div style={wrap}>
        <div style={emptyBox} role="status" aria-live="polite">
          Loading HDRIs…
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={wrap}>
        <div style={emptyBox} role="alert">
          <span>HDRI list unavailable: {error}</span>
          {onRetry && (
            <button type="button" onClick={onRetry} style={retryBtn}>
              Retry
            </button>
          )}
        </div>
      </div>
    )
  }

  if (hdris.length === 0) {
    return (
      <div style={wrap}>
        <div style={emptyBox}>
          <span>No HDRIs available.</span>
          {onRetry && (
            <button type="button" onClick={onRetry} style={retryBtn}>
              Retry
            </button>
          )}
        </div>
      </div>
    )
  }

  return (
    <div style={{ ...wrap, opacity: enabled ? 1 : 0.55, transition: 'opacity 0.15s' }}>
      <div style={grid} role="radiogroup" aria-label="HDRI lighting">
        {hdris.map(h => {
          const isSelected = selectedId === h.id
          const style: CSSProperties = {
            ...thumbBase,
            ...(isSelected ? thumbSelected : {}),
          }
          return (
            <div
              key={h.id}
              style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}
            >
              <button
                type="button"
                role="radio"
                aria-checked={isSelected}
                aria-label={`HDRI: ${h.name}`}
                title={h.name}
                onClick={() => onSelect(h.id)}
                style={style}
              >
                <img
                  src={`data:image/png;base64,${h.thumbnail_b64}`}
                  alt=""
                  style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                />
                {isSelected && (
                  <span style={checkBadge} aria-hidden="true">
                    ✓
                  </span>
                )}
              </button>
              <span style={captionStyle}>{h.name}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
