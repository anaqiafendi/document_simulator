import { useState } from 'react'
import type { RespondentConfig, FieldTypeConfig, ZoneConfig } from '../types'
import InkColorPicker from './InkColorPicker'
import FontSelect from './FontSelect'
import { getRespondentColor } from '../utils/colors'
import { FAKER_PROVIDERS } from '../utils/faker'

interface Props {
  respondents: RespondentConfig[]
  zones: ZoneConfig[]
  selectedZoneId: string | null
  zonePreviews: Record<string, { text: string; dx: number; dy: number }>
  onAdd: () => void
  onRemove: (id: string) => void
  onUpdate: (id: string, patch: Partial<RespondentConfig>) => void
  onAddFieldType: (respondentId: string) => void
  onRemoveFieldType: (respondentId: string, ftId: string) => void
  onUpdateFieldType: (respondentId: string, ftId: string, patch: Partial<FieldTypeConfig>) => void
  onSelectZone: (id: string) => void
  onUpdateZone: (id: string, patch: Partial<ZoneConfig>) => void
  onRemoveZone: (id: string) => void
  onRerollZone: (zone_id: string, provider: string) => void
}

const rowStyle: React.CSSProperties = { display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', marginBottom: 6 }
const labelStyle: React.CSSProperties = { fontSize: 11, color: '#888', minWidth: 68 }

// ── Field-type card (collapsible) ────────────────────────────────────────────
function FieldTypeCard({
  ft,
  canRemove,
  onRemove,
  onUpdate,
}: {
  ft: FieldTypeConfig
  canRemove: boolean
  onRemove: () => void
  onUpdate: (patch: Partial<FieldTypeConfig>) => void
}) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div style={{ marginBottom: 5, border: '1px solid #ececec', borderRadius: 4, overflow: 'hidden' }}>
      <div
        onClick={() => setExpanded(e => !e)}
        style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 10px', cursor: 'pointer', background: expanded ? '#f0f4ff' : '#fafafa', userSelect: 'none' }}
      >
        <span style={{ fontSize: 10, color: '#bbb', width: 10 }}>{expanded ? '▾' : '▸'}</span>
        <input
          value={ft.display_name}
          onChange={e => onUpdate({ display_name: e.target.value })}
          onClick={e => e.stopPropagation()}
          style={{ flex: 1, fontWeight: 500, border: 'none', outline: 'none', background: 'transparent', fontSize: 12 }}
        />
        <span style={{ fontFamily: ft.font_family, fontSize: 13, color: '#666', pointerEvents: 'none' }}>Aa</span>
        <span style={{ width: 12, height: 12, borderRadius: '50%', background: ft.font_color, border: '1px solid #ddd', flexShrink: 0 }} />
        {canRemove && (
          <button onClick={e => { e.stopPropagation(); onRemove() }}
            style={{ color: '#ccc', border: 'none', background: 'none', cursor: 'pointer', fontSize: 14, padding: 0, lineHeight: 1 }}>
            &times;
          </button>
        )}
      </div>

      {expanded && (
        <div style={{ padding: '10px 12px', background: 'white' }}>
          <div style={rowStyle}>
            <span style={labelStyle}>Ink color</span>
            <InkColorPicker value={ft.font_color} onChange={v => onUpdate({ font_color: v })} />
          </div>
          <div style={rowStyle}>
            <span style={labelStyle}>Font</span>
            <FontSelect value={ft.font_family} onChange={v => onUpdate({ font_family: v as FieldTypeConfig['font_family'] })} />
            <label style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 3 }}>
              <input type="checkbox" checked={ft.bold} onChange={e => onUpdate({ bold: e.target.checked })} /> B
            </label>
            <label style={{ fontSize: 12, fontStyle: 'italic', display: 'flex', alignItems: 'center', gap: 3 }}>
              <input type="checkbox" checked={ft.italic} onChange={e => onUpdate({ italic: e.target.checked })} /> I
            </label>
          </div>
          <div style={rowStyle}>
            <span style={labelStyle}>Fill style</span>
            <select value={ft.fill_style} onChange={e => onUpdate({ fill_style: e.target.value as FieldTypeConfig['fill_style'] })} style={{ fontSize: 12 }}>
              <option value="typed">Typed</option>
              <option value="form-fill">Form fill</option>
              <option value="handwritten-font">Handwritten font</option>
              <option value="stamp">Stamp</option>
            </select>
          </div>
          <div style={rowStyle}>
            <span style={labelStyle}>Font size</span>
            <input type="number" min={6} max={72} value={ft.font_size_range[0]}
              onChange={e => onUpdate({ font_size_range: [Number(e.target.value), ft.font_size_range[1]] })}
              style={{ width: 48, fontSize: 12 }} />
            <span style={{ fontSize: 12, color: '#aaa' }}>–</span>
            <input type="number" min={6} max={72} value={ft.font_size_range[1]}
              onChange={e => onUpdate({ font_size_range: [ft.font_size_range[0], Number(e.target.value)] })}
              style={{ width: 48, fontSize: 12 }} />
            <span style={{ fontSize: 12, color: '#aaa' }}>pt</span>
          </div>
          <div style={rowStyle}>
            <span style={labelStyle}>Jitter X</span>
            <input type="number" min={0} max={1} step={0.01} value={ft.jitter_x}
              onChange={e => onUpdate({ jitter_x: Number(e.target.value) })} style={{ width: 56, fontSize: 12 }} />
            <span style={labelStyle}>Jitter Y</span>
            <input type="number" min={0} max={1} step={0.01} value={ft.jitter_y}
              onChange={e => onUpdate({ jitter_y: Number(e.target.value) })} style={{ width: 56, fontSize: 12 }} />
          </div>
        </div>
      )}
    </div>
  )
}

// ── Zone row inside respondent card ──────────────────────────────────────────
function ZoneRow({
  zone,
  color,
  isSelected,
  previewText,
  respondent,
  onSelect,
  onUpdate,
  onRemove,
  onReroll,
}: {
  zone: ZoneConfig
  color: string
  isSelected: boolean
  previewText: string
  respondent: RespondentConfig
  onSelect: () => void
  onUpdate: (patch: Partial<ZoneConfig>) => void
  onRemove: () => void
  onReroll: () => void
}) {
  return (
    <div
      onClick={onSelect}
      style={{
        border: `1px solid ${isSelected ? color : '#e8e8e8'}`,
        borderLeft: `3px solid ${color}`,
        borderRadius: 3,
        padding: '6px 8px',
        marginBottom: 5,
        cursor: 'pointer',
        background: isSelected ? color + '10' : 'white',
      }}
    >
      <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
        <input
          value={zone.label}
          onChange={e => onUpdate({ label: e.target.value })}
          onClick={e => e.stopPropagation()}
          style={{ flex: 1, fontWeight: 600, border: 'none', outline: 'none', background: 'transparent', fontSize: 12, borderBottom: '1px solid #eee' }}
        />
        {/* Re-roll */}
        <button
          title="Re-roll preview text"
          onClick={e => { e.stopPropagation(); onReroll() }}
          style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 14, color: '#3498db', padding: '0 2px' }}
        >
          &#8635;
        </button>
        <button
          onClick={e => { e.stopPropagation(); onRemove() }}
          style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 15, color: '#ccc', padding: 0, lineHeight: 1 }}
          title="Delete zone"
        >
          &times;
        </button>
      </div>

      {/* Controls row */}
      <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', alignItems: 'center', marginTop: 5 }} onClick={e => e.stopPropagation()}>
        <select value={zone.field_type_id}
          onChange={e => onUpdate({ field_type_id: e.target.value })}
          style={{ fontSize: 11, maxWidth: 80 }} title="Writing style">
          {respondent.field_types.map(ft => <option key={ft.field_type_id} value={ft.field_type_id}>{ft.display_name}</option>)}
        </select>

        <select value={zone.faker_provider}
          onChange={e => { onUpdate({ faker_provider: e.target.value }); onReroll() }}
          style={{ fontSize: 11, maxWidth: 110 }} title="Data type">
          {FAKER_PROVIDERS.map(p => <option key={p.key} value={p.key}>{p.label}</option>)}
        </select>

        <select value={zone.alignment}
          onChange={e => onUpdate({ alignment: e.target.value as ZoneConfig['alignment'] })}
          style={{ fontSize: 11, width: 55 }}>
          <option value="left">left</option>
          <option value="center">center</option>
          <option value="right">right</option>
        </select>
      </div>

      {/* Preview text */}
      {previewText && (
        <div style={{
          marginTop: 5, fontSize: 11, color: '#444', fontStyle: 'italic',
          background: '#fafafa', padding: '3px 5px', borderRadius: 3, wordBreak: 'break-word',
        }}>
          {previewText}
        </div>
      )}

      {/* Coordinates */}
      <div style={{ fontSize: 10, color: '#ccc', marginTop: 3 }}>
        {Math.round(zone.box[0][0])},{Math.round(zone.box[0][1])} &nbsp;
        {Math.round(zone.box[2][0] - zone.box[0][0])}&times;{Math.round(zone.box[2][1] - zone.box[0][1])}
      </div>
    </div>
  )
}

// ── Respondent card ───────────────────────────────────────────────────────────
function RespondentCard({
  r,
  color,
  respondentZones,
  selectedZoneId,
  zonePreviews,
  canRemove,
  onRemove,
  onUpdate,
  onAddFieldType,
  onRemoveFieldType,
  onUpdateFieldType,
  onSelectZone,
  onUpdateZone,
  onRemoveZone,
  onRerollZone,
}: {
  r: RespondentConfig
  color: string
  respondentZones: ZoneConfig[]
  selectedZoneId: string | null
  zonePreviews: Record<string, { text: string; dx: number; dy: number }>
  canRemove: boolean
  onRemove: () => void
  onUpdate: (patch: Partial<RespondentConfig>) => void
  onAddFieldType: () => void
  onRemoveFieldType: (ftId: string) => void
  onUpdateFieldType: (ftId: string, patch: Partial<FieldTypeConfig>) => void
  onSelectZone: (id: string) => void
  onUpdateZone: (id: string, patch: Partial<ZoneConfig>) => void
  onRemoveZone: (id: string) => void
  onRerollZone: (zone_id: string, provider: string) => void
}) {
  const [stylesOpen, setStylesOpen] = useState(true)
  const [zonesOpen, setZonesOpen] = useState(true)

  return (
    <div style={{ border: `1px solid #ddd`, borderLeft: `4px solid ${color}`, borderRadius: 5, overflow: 'hidden', marginBottom: 10 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '9px 12px', background: '#f8f8f8' }}>
        <span style={{ width: 12, height: 12, borderRadius: '50%', background: color, flexShrink: 0 }} />
        <input
          value={r.display_name}
          onChange={e => onUpdate({ display_name: e.target.value })}
          style={{ flex: 1, fontWeight: 600, fontSize: 13, border: 'none', outline: 'none', background: 'transparent', borderBottom: '1px solid #e0e0e0' }}
        />
        {canRemove && (
          <button onClick={onRemove} style={{ color: '#e74c3c', border: 'none', background: 'none', cursor: 'pointer', fontSize: 12 }}>
            Remove
          </button>
        )}
      </div>

      <div style={{ padding: '8px 12px' }}>
        {/* Writing styles accordion */}
        <div onClick={() => setStylesOpen(o => !o)}
          style={{ display: 'flex', alignItems: 'center', gap: 5, cursor: 'pointer', userSelect: 'none', fontSize: 12, color: '#666', marginBottom: stylesOpen ? 7 : 0 }}>
          <span style={{ fontSize: 9, color: '#bbb' }}>{stylesOpen ? '▾' : '▸'}</span>
          Writing styles ({r.field_types.length})
        </div>
        {stylesOpen && (
          <>
            {r.field_types.map(ft => (
              <FieldTypeCard
                key={ft.field_type_id}
                ft={ft}
                canRemove={r.field_types.length > 1}
                onRemove={() => onRemoveFieldType(ft.field_type_id)}
                onUpdate={patch => onUpdateFieldType(ft.field_type_id, patch)}
              />
            ))}
            <button onClick={onAddFieldType}
              style={{ fontSize: 11, color: '#3498db', border: '1px dashed #3498db', background: 'none', borderRadius: 3, padding: '3px 10px', cursor: 'pointer', width: '100%', marginBottom: 8 }}>
              + Add writing style
            </button>
          </>
        )}

        {/* Zones accordion */}
        <div onClick={() => setZonesOpen(o => !o)}
          style={{ display: 'flex', alignItems: 'center', gap: 5, cursor: 'pointer', userSelect: 'none', fontSize: 12, color: '#666', marginBottom: zonesOpen ? 7 : 0, marginTop: 4 }}>
          <span style={{ fontSize: 9, color: '#bbb' }}>{zonesOpen ? '▾' : '▸'}</span>
          Zones ({respondentZones.length})
        </div>
        {zonesOpen && (
          respondentZones.length === 0
            ? <p style={{ fontSize: 11, color: '#bbb', margin: '0 0 6px 0' }}>No zones assigned — draw on the canvas in Draw mode.</p>
            : respondentZones.map(zone => (
              <ZoneRow
                key={zone.zone_id}
                zone={zone}
                color={color}
                isSelected={zone.zone_id === selectedZoneId}
                previewText={zonePreviews[zone.zone_id]?.text ?? ''}
                respondent={r}
                onSelect={() => onSelectZone(zone.zone_id)}
                onUpdate={patch => onUpdateZone(zone.zone_id, patch)}
                onRemove={() => onRemoveZone(zone.zone_id)}
                onReroll={() => onRerollZone(zone.zone_id, zone.faker_provider)}
              />
            ))
        )}
      </div>
    </div>
  )
}

// ── Main export ───────────────────────────────────────────────────────────────
export default function RespondentPanel({
  respondents, zones, selectedZoneId, zonePreviews,
  onAdd, onRemove, onUpdate,
  onAddFieldType, onRemoveFieldType, onUpdateFieldType,
  onSelectZone, onUpdateZone, onRemoveZone, onRerollZone,
}: Props) {
  return (
    <div>
      {respondents.map((r, idx) => (
        <RespondentCard
          key={r.respondent_id}
          r={r}
          color={getRespondentColor(idx)}
          respondentZones={zones.filter(z => z.respondent_id === r.respondent_id)}
          selectedZoneId={selectedZoneId}
          zonePreviews={zonePreviews}
          canRemove={respondents.length > 1}
          onRemove={() => onRemove(r.respondent_id)}
          onUpdate={patch => onUpdate(r.respondent_id, patch)}
          onAddFieldType={() => onAddFieldType(r.respondent_id)}
          onRemoveFieldType={ftId => onRemoveFieldType(r.respondent_id, ftId)}
          onUpdateFieldType={(ftId, patch) => onUpdateFieldType(r.respondent_id, ftId, patch)}
          onSelectZone={onSelectZone}
          onUpdateZone={onUpdateZone}
          onRemoveZone={onRemoveZone}
          onRerollZone={onRerollZone}
        />
      ))}
      <button onClick={onAdd}
        style={{ width: '100%', padding: '7px 0', fontSize: 13, cursor: 'pointer', border: '1px dashed #aaa', borderRadius: 4, background: 'none', color: '#666' }}>
        + Add respondent
      </button>
    </div>
  )
}

import React from 'react'
