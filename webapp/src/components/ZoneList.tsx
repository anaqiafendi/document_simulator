import { useEffect, useRef } from 'react'
import type { ZoneConfig, RespondentConfig } from '../types'

const FAKER_PROVIDERS = [
  'name', 'first_name', 'last_name', 'email', 'phone_number',
  'address', 'city', 'postcode', 'company', 'date_of_birth',
  'ssn', 'credit_card_number', 'sentence', 'word', 'custom',
]

const ZONE_COLORS = [
  '#e74c3c', '#3498db', '#2ecc71', '#f39c12',
  '#9b59b6', '#1abc9c', '#e67e22', '#e91e63',
]
const zoneColor = (i: number) => ZONE_COLORS[i % ZONE_COLORS.length]

interface Props {
  zones: ZoneConfig[]
  selectedId: string | null
  respondents: RespondentConfig[]
  onSelect: (id: string) => void
  onUpdate: (id: string, patch: Partial<ZoneConfig>) => void
  onRemove: (id: string) => void
}

export default function ZoneList({ zones, selectedId, respondents, onSelect, onUpdate, onRemove }: Props) {
  const rowRefs = useRef<Map<string, HTMLDivElement>>(new Map())

  // Scroll the selected zone into view whenever selectedId changes
  useEffect(() => {
    if (!selectedId) return
    const el = rowRefs.current.get(selectedId)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }, [selectedId])

  if (zones.length === 0) {
    return (
      <p style={{ color: '#aaa', fontSize: 13, margin: 0 }}>
        No zones yet — switch to Draw mode and drag rectangles on the canvas.
      </p>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {zones.map((zone, i) => {
        const isSelected = zone.zone_id === selectedId
        const color = zoneColor(i)
        const respondent = respondents.find(r => r.respondent_id === zone.respondent_id)
        const fieldTypes = respondent?.field_types ?? []
        const x = Math.round(zone.box[0][0])
        const y = Math.round(zone.box[0][1])
        const w = Math.round(zone.box[2][0] - zone.box[0][0])
        const h = Math.round(zone.box[2][1] - zone.box[0][1])

        return (
          <div
            key={zone.zone_id}
            ref={node => {
              if (node) rowRefs.current.set(zone.zone_id, node)
              else rowRefs.current.delete(zone.zone_id)
            }}
            onClick={() => onSelect(zone.zone_id)}
            style={{
              border: `1px solid ${isSelected ? color : '#e0e0e0'}`,
              borderLeft: `4px solid ${color}`,
              borderRadius: 5,
              padding: '8px 10px',
              cursor: 'pointer',
              background: isSelected ? color + '12' : 'white',
              boxShadow: isSelected ? `0 0 0 2px ${color}44` : 'none',
              transition: 'box-shadow 0.15s, background 0.15s',
            }}
          >
            {/* Row 1: label + delete */}
            <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 6 }}>
              <span
                style={{
                  width: 10, height: 10, borderRadius: 2,
                  background: color, flexShrink: 0, display: 'inline-block',
                }}
              />
              <input
                value={zone.label}
                onChange={e => onUpdate(zone.zone_id, { label: e.target.value })}
                onClick={e => e.stopPropagation()}
                placeholder="Label"
                style={{
                  flex: 1, fontWeight: 600, border: 'none', outline: 'none',
                  borderBottom: '1px solid #e0e0e0', fontSize: 13, background: 'transparent',
                }}
              />
              <button
                onClick={e => { e.stopPropagation(); onRemove(zone.zone_id) }}
                style={{
                  color: '#bbb', border: 'none', background: 'none',
                  cursor: 'pointer', fontSize: 16, lineHeight: 1, padding: 0,
                }}
                title="Delete zone"
              >
                &times;
              </button>
            </div>

            {/* Row 2: controls */}
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
              <select
                value={zone.respondent_id}
                onChange={e => {
                  const r = respondents.find(r => r.respondent_id === e.target.value)
                  onUpdate(zone.zone_id, {
                    respondent_id: e.target.value,
                    field_type_id: r?.field_types[0]?.field_type_id ?? zone.field_type_id,
                  })
                }}
                onClick={e => e.stopPropagation()}
                style={{ fontSize: 11, maxWidth: 90 }}
                title="Respondent"
              >
                {respondents.map(r => (
                  <option key={r.respondent_id} value={r.respondent_id}>{r.display_name}</option>
                ))}
              </select>

              <select
                value={zone.field_type_id}
                onChange={e => onUpdate(zone.zone_id, { field_type_id: e.target.value })}
                onClick={e => e.stopPropagation()}
                style={{ fontSize: 11, maxWidth: 80 }}
                title="Writing style"
              >
                {fieldTypes.map(ft => (
                  <option key={ft.field_type_id} value={ft.field_type_id}>{ft.display_name}</option>
                ))}
              </select>

              <select
                value={zone.faker_provider}
                onChange={e => onUpdate(zone.zone_id, { faker_provider: e.target.value })}
                onClick={e => e.stopPropagation()}
                style={{ fontSize: 11, maxWidth: 100 }}
                title="Data provider"
              >
                {FAKER_PROVIDERS.map(p => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>

              <select
                value={zone.alignment}
                onChange={e => onUpdate(zone.zone_id, { alignment: e.target.value as ZoneConfig['alignment'] })}
                onClick={e => e.stopPropagation()}
                style={{ fontSize: 11, width: 58 }}
                title="Alignment"
              >
                <option value="left">left</option>
                <option value="center">center</option>
                <option value="right">right</option>
              </select>
            </div>

            {/* Row 3: coords */}
            <div style={{ fontSize: 10, color: '#bbb', marginTop: 5 }}>
              x={x} y={y} &nbsp;{w}&times;{h}px
            </div>
          </div>
        )
      })}
    </div>
  )
}
