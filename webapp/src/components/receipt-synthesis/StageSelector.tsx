import type { CSSProperties } from 'react'
import type { CoordSnapshotStage } from '../../types'

interface StageSelectorProps {
  /** Currently-overlaid CoordSnapshot stage. */
  value: CoordSnapshotStage
  /** Update the overlay stage. */
  onChange: (stage: CoordSnapshotStage) => void
  /** When true, renders a small "auto" badge to communicate that the value
   *  follows the current pipeline-stage card (no manual override). */
  isAuto?: boolean
  /** Reset back to the auto-tracked stage. Hidden when `isAuto` is true. */
  onReset?: () => void
  /** Optional id for the underlying <select>; the inspector pairs it with a
   *  <label htmlFor>. */
  id?: string
  /** Disable interaction (e.g. while no response is loaded). */
  disabled?: boolean
}

interface StageOption {
  value: CoordSnapshotStage
  label: string
}

// The append-only coords trail. Order matches the pipeline progression so the
// dropdown reads top-to-bottom in render order.
const STAGE_OPTIONS: StageOption[] = [
  { value: 'html', label: 'HTML (pre-raster)' },
  { value: 'raster', label: 'Raster' },
  { value: 'uv', label: 'UV' },
  { value: 'world', label: 'World (xy projection)' },
  { value: 'camera_2d', label: 'Camera 2D' },
  { value: 'camera_fx', label: 'Camera FX' },
  { value: 'final_crop', label: 'Final crop' },
]

const wrap: CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: 6,
}

const labelStyle: CSSProperties = {
  fontSize: 12,
  fontWeight: 600,
  color: '#555',
}

const select: CSSProperties = {
  fontSize: 12,
  padding: '3px 6px',
  borderRadius: 4,
  border: '1px solid #ccc',
  background: '#fff',
  minWidth: 150,
}

const autoBadge: CSSProperties = {
  fontSize: 9,
  fontWeight: 700,
  letterSpacing: '0.05em',
  textTransform: 'uppercase',
  color: '#888',
  background: '#f0f0f0',
  border: '1px solid #e0e0e0',
  borderRadius: 8,
  padding: '1px 6px',
}

const resetBtn: CSSProperties = {
  fontSize: 11,
  padding: '2px 8px',
  borderRadius: 4,
  border: '1px solid #ccc',
  background: '#fafafa',
  cursor: 'pointer',
  color: '#333',
}

export default function StageSelector({
  value,
  onChange,
  isAuto = false,
  onReset,
  id = 'rs-stage-selector',
  disabled = false,
}: StageSelectorProps) {
  return (
    <div style={wrap}>
      <label style={labelStyle} htmlFor={id}>Overlay stage:</label>
      <select
        id={id}
        value={value}
        onChange={e => onChange(e.target.value as CoordSnapshotStage)}
        disabled={disabled}
        style={select}
        title="Choose which CoordSnapshot stage's polygons to overlay on the current image."
      >
        {STAGE_OPTIONS.map(o => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
      {isAuto ? (
        <span style={autoBadge} title="Tracks the selected pipeline card automatically.">auto</span>
      ) : onReset ? (
        <button
          type="button"
          onClick={onReset}
          style={resetBtn}
          title="Re-sync overlay stage with the selected pipeline card."
        >
          auto
        </button>
      ) : null}
    </div>
  )
}
