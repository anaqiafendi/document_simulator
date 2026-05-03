import type { CSSProperties } from 'react'

export interface PipelineStageCardProps {
  stageId: string
  label: string
  emoji: string
  thumbnailB64?: string | null
  badge?: string | null
  selected?: boolean
  /** Hard-disabled — the card is unclickable (used for Camera FX in v0.3). */
  disabled?: boolean
  disabledReason?: string
  /** Soft hint shown under the thumbnail when the card *is* clickable but the
   *  underlying stage hasn't been rendered yet (used for the 3D Scene card
   *  when `render_3d=false`). Ignored when `disabled` is true. */
  hint?: string | null
  onClick?: () => void
}

const cardBase: CSSProperties = {
  flex: '0 0 140px',
  width: 140,
  borderRadius: 8,
  border: '2px solid #e8e8e8',
  background: '#fff',
  padding: '10px 10px 8px',
  cursor: 'pointer',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'stretch',
  gap: 6,
  fontFamily: 'system-ui, sans-serif',
  transition: 'border-color 0.15s, background 0.15s, box-shadow 0.15s',
  position: 'relative',
}

const cardSelected: CSSProperties = {
  borderColor: '#4f6ef7',
  background: '#f0f4ff',
  boxShadow: '0 1px 6px rgba(79,110,247,0.18)',
}

const cardDisabled: CSSProperties = {
  cursor: 'not-allowed',
  opacity: 0.55,
  background: '#f4f4f6',
}

const thumbBox: CSSProperties = {
  width: '100%',
  height: 80,
  borderRadius: 4,
  background: '#fafafa',
  border: '1px solid #eee',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  overflow: 'hidden',
  fontSize: 28,
}

export default function PipelineStageCard({
  label,
  emoji,
  thumbnailB64,
  badge,
  selected = false,
  disabled = false,
  disabledReason,
  hint = null,
  onClick,
}: PipelineStageCardProps) {
  const style: CSSProperties = {
    ...cardBase,
    ...(selected ? cardSelected : {}),
    ...(disabled ? cardDisabled : {}),
  }

  const handleClick = () => {
    if (disabled) return
    onClick?.()
  }

  // Show the soft hint when not disabled (and a hint string is provided).
  const showHint = !disabled && !!hint
  // Show the disabled note when actually disabled.
  const showDisabledNote = disabled

  return (
    <div
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-label={`Stage: ${label}`}
      aria-disabled={disabled}
      aria-pressed={selected}
      onClick={handleClick}
      onKeyDown={e => {
        if (disabled) return
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onClick?.()
        }
      }}
      title={disabled ? disabledReason ?? `${label} (not yet available)` : hint ?? label}
      style={style}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: selected ? '#4f6ef7' : '#333' }}>{label}</span>
        {badge && (
          <span style={{
            fontSize: 10,
            fontWeight: 700,
            color: '#4f6ef7',
            background: '#eef1ff',
            border: '1px solid #d6dffb',
            borderRadius: 10,
            padding: '1px 6px',
            whiteSpace: 'nowrap',
          }}>{badge}</span>
        )}
      </div>
      <div style={thumbBox}>
        {thumbnailB64 ? (
          <img
            src={`data:image/png;base64,${thumbnailB64}`}
            alt={`${label} thumbnail`}
            style={{ width: '100%', height: '100%', objectFit: 'contain' }}
          />
        ) : (
          <span aria-hidden="true">{emoji}</span>
        )}
      </div>
      {showDisabledNote && (
        <span style={{ fontSize: 10, color: '#888', fontStyle: 'italic', textAlign: 'center' }}>
          {disabledReason ?? 'Coming soon'}
        </span>
      )}
      {showHint && (
        <span style={{ fontSize: 10, color: '#4f6ef7', fontStyle: 'italic', textAlign: 'center' }}>
          {hint}
        </span>
      )}
    </div>
  )
}
