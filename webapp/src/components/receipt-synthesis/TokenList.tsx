import type { CSSProperties } from 'react'
import type { TokenGroundTruth } from '../../types'
import { colorForToken } from './BboxOverlay'

interface TokenListProps {
  tokens: TokenGroundTruth[]
  highlightTokenId?: string | null
  onSelectToken?: (tokenId: string) => void
}

const wrap: CSSProperties = {
  border: '1px solid #e8e8e8',
  borderRadius: 6,
  background: '#fff',
  overflow: 'hidden',
}

const tableStyle: CSSProperties = {
  width: '100%',
  borderCollapse: 'collapse',
  fontSize: 12,
  fontFamily: 'system-ui, sans-serif',
}

const thStyle: CSSProperties = {
  background: '#fafafa',
  textAlign: 'left',
  padding: '6px 10px',
  fontWeight: 700,
  color: '#555',
  borderBottom: '1px solid #e8e8e8',
  position: 'sticky',
  top: 0,
}

const tdStyle: CSSProperties = {
  padding: '5px 10px',
  borderBottom: '1px solid #f3f3f5',
  verticalAlign: 'top',
}

const swatch: CSSProperties = {
  display: 'inline-block',
  width: 10,
  height: 10,
  borderRadius: 2,
  marginRight: 6,
  verticalAlign: 'middle',
}

export default function TokenList({
  tokens,
  highlightTokenId = null,
  onSelectToken,
}: TokenListProps) {
  if (tokens.length === 0) {
    return (
      <div style={{ ...wrap, padding: 20, textAlign: 'center', color: '#999', fontSize: 13 }}>
        No tokens in ground truth.
      </div>
    )
  }

  return (
    <div style={{ ...wrap, maxHeight: 360, overflowY: 'auto' }}>
      <table style={tableStyle}>
        <thead>
          <tr>
            <th style={thStyle}>Token ID</th>
            <th style={thStyle}>Text</th>
            <th style={thStyle}>Role</th>
          </tr>
        </thead>
        <tbody>
          {tokens.map(t => {
            const isHi = t.token_id === highlightTokenId
            const colour = colorForToken(t.token_id)
            const rowStyle: CSSProperties = {
              cursor: onSelectToken ? 'pointer' : 'default',
              background: isHi ? '#fff8c4' : 'transparent',
              transition: 'background 0.1s',
            }
            return (
              <tr
                key={t.token_id}
                onClick={onSelectToken ? () => onSelectToken(t.token_id) : undefined}
                style={rowStyle}
              >
                <td style={{ ...tdStyle, fontFamily: 'monospace', whiteSpace: 'nowrap' }}>
                  <span style={{ ...swatch, background: colour }} aria-hidden="true" />
                  {t.token_id}
                </td>
                <td style={{ ...tdStyle, maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {t.text}
                </td>
                <td style={{ ...tdStyle, color: '#666', fontStyle: t.semantic_role ? 'normal' : 'italic' }}>
                  {t.semantic_role ?? '—'}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
