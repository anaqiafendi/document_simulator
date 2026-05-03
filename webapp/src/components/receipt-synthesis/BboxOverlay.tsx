import { useEffect, useRef, useState } from 'react'
import type { CoordSnapshotStage, TokenGroundTruth } from '../../types'

// 8-distinct-hue palette — token color is stable across renders for the same
// token_id (hash → palette index).
const PALETTE = [
  '#e74c3c', // red
  '#3498db', // blue
  '#2ecc71', // green
  '#9b59b6', // purple
  '#f39c12', // orange
  '#1abc9c', // teal
  '#e67e22', // amber
  '#34495e', // slate
]

function hashStr(s: string): number {
  let h = 0
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) - h + s.charCodeAt(i)) | 0
  }
  return Math.abs(h)
}

export function colorForToken(tokenId: string): string {
  return PALETTE[hashStr(tokenId) % PALETTE.length]
}

interface BboxOverlayProps {
  imageB64: string
  tokens: TokenGroundTruth[]
  stage: CoordSnapshotStage
  showBboxes: boolean
  showLabels: boolean
  highlightTokenId?: string | null
  onSelectToken?: (tokenId: string) => void
}

export default function BboxOverlay({
  imageB64,
  tokens,
  stage,
  showBboxes,
  showLabels,
  highlightTokenId = null,
  onSelectToken,
}: BboxOverlayProps) {
  const imgRef = useRef<HTMLImageElement>(null)
  const [natural, setNatural] = useState<{ w: number; h: number } | null>(null)

  // Reset natural size when the image source changes
  useEffect(() => {
    setNatural(null)
  }, [imageB64])

  const handleLoad = () => {
    const el = imgRef.current
    if (!el) return
    setNatural({ w: el.naturalWidth, h: el.naturalHeight })
  }

  const viewBox = natural ? `0 0 ${natural.w} ${natural.h}` : undefined

  return (
    <div style={{ position: 'relative', display: 'inline-block', maxWidth: '100%' }}>
      <img
        ref={imgRef}
        src={`data:image/png;base64,${imageB64}`}
        alt="Stage preview"
        onLoad={handleLoad}
        style={{
          display: 'block',
          maxWidth: '100%',
          height: 'auto',
          borderRadius: 4,
          border: '1px solid #ddd',
        }}
      />
      {showBboxes && natural && (
        <svg
          viewBox={viewBox}
          preserveAspectRatio="none"
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            pointerEvents: onSelectToken ? 'auto' : 'none',
          }}
        >
          {tokens.map(t => {
            const snap = t.coords.find(c => c.stage === stage)
            if (!snap || !snap.polygon || snap.polygon.length === 0) return null
            const points = snap.polygon.map(([x, y]) => `${x},${y}`).join(' ')
            const colour = colorForToken(t.token_id)
            const isHi = highlightTokenId === t.token_id
            const stroke = isHi ? '#ffeb3b' : colour
            const sw = isHi ? Math.max(natural.w, natural.h) * 0.004 : Math.max(natural.w, natural.h) * 0.0018
            const fill = isHi ? `${colour}44` : 'none'
            const labelX = snap.polygon[0][0]
            const labelY = Math.max(snap.polygon[0][1] - natural.h * 0.005, natural.h * 0.012)
            return (
              <g key={t.token_id} onClick={onSelectToken ? () => onSelectToken(t.token_id) : undefined}
                 style={{ cursor: onSelectToken ? 'pointer' : 'default' }}>
                <polygon
                  points={points}
                  fill={fill}
                  stroke={stroke}
                  strokeWidth={sw}
                  strokeLinejoin="round"
                />
                {showLabels && (
                  <text
                    x={labelX}
                    y={labelY}
                    fontSize={Math.max(natural.h * 0.014, 8)}
                    fill={stroke}
                    style={{
                      paintOrder: 'stroke',
                      stroke: 'rgba(255,255,255,0.85)',
                      strokeWidth: 1.5,
                      strokeLinejoin: 'round',
                      fontFamily: 'system-ui, sans-serif',
                      fontWeight: 600,
                    }}
                  >
                    {t.token_id}
                  </text>
                )}
              </g>
            )
          })}
        </svg>
      )}
    </div>
  )
}
