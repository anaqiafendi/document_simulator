import { useEffect, useRef, useState } from 'react'
import Konva from 'konva'
import { Stage, Layer, Image as KonvaImage, Rect, Text, Group, Transformer } from 'react-konva'
import type { TemplateInfo, ZoneConfig, RespondentConfig } from '../types'
import type { ZonePreviewData } from '../hooks/useZonePreview'
import { getRespondentColor } from '../utils/colors'

const FONT_FAMILY_MAP: Record<string, string> = {
  'sans-serif':  'Arial',
  'serif':       'Georgia',
  'monospace':   'Courier New',
  'handwriting': 'cursive',
}

function boxToRect(box: number[][]) {
  const x = Math.min(box[0][0], box[2][0])
  const y = Math.min(box[0][1], box[2][1])
  const w = Math.abs(box[2][0] - box[0][0])
  const h = Math.abs(box[2][1] - box[0][1])
  return { x, y, w, h }
}

function rectToBox(x: number, y: number, w: number, h: number): number[][] {
  return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
}

interface Props {
  templateInfo: TemplateInfo
  zones: ZoneConfig[]
  selectedId: string | null
  respondents: RespondentConfig[]
  zonePreviews: Record<string, ZonePreviewData>
  onZoneDrawn: (partial: Omit<ZoneConfig, 'zone_id'>) => void
  onZoneSelect: (id: string | null) => void
  onZoneUpdate: (id: string, patch: Partial<ZoneConfig>) => void
}

export default function ZoneCanvas({
  templateInfo,
  zones,
  selectedId,
  respondents,
  zonePreviews,
  onZoneDrawn,
  onZoneSelect,
  onZoneUpdate,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const stageRef = useRef<Konva.Stage>(null)
  const transformerRef = useRef<Konva.Transformer>(null)
  const zoneRefs = useRef<Map<string, Konva.Rect>>(new Map())

  const [stageWidth, setStageWidth] = useState(800)
  const [bgImage, setBgImage] = useState<HTMLImageElement | null>(null)
  const [mode, setMode] = useState<'draw' | 'select'>('draw')
  const [drawing, setDrawing] = useState<{ x: number; y: number; w: number; h: number } | null>(null)
  const drawStart = useRef<{ x: number; y: number } | null>(null)

  const [activeRespondentId, setActiveRespondentId] = useState(respondents[0]?.respondent_id ?? 'default')
  const [activeFieldTypeId, setActiveFieldTypeId] = useState(respondents[0]?.field_types[0]?.field_type_id ?? 'standard')

  const displayScale = stageWidth / templateInfo.width_px
  const stageHeight = Math.round(templateInfo.height_px * displayScale)

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const update = () => setStageWidth(el.clientWidth || 800)
    update()
    const obs = new ResizeObserver(update)
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  useEffect(() => {
    const img = new Image()
    img.onload = () => setBgImage(img)
    img.src = `data:image/png;base64,${templateInfo.image_b64}`
  }, [templateInfo.image_b64])

  useEffect(() => {
    const tr = transformerRef.current
    if (!tr) return
    if (selectedId && mode === 'select') {
      const node = zoneRefs.current.get(selectedId)
      tr.nodes(node ? [node] : [])
    } else {
      tr.nodes([])
    }
    tr.getLayer()?.batchDraw()
  }, [selectedId, mode, zones])

  useEffect(() => {
    if (!respondents.find(r => r.respondent_id === activeRespondentId)) {
      const r = respondents[0]
      if (r) {
        setActiveRespondentId(r.respondent_id)
        setActiveFieldTypeId(r.field_types[0]?.field_type_id ?? 'standard')
      }
    }
  }, [respondents, activeRespondentId])

  const getDocPos = () => {
    const pos = stageRef.current?.getPointerPosition()
    if (!pos) return null
    return { x: pos.x / displayScale, y: pos.y / displayScale }
  }

  const handleMouseDown = (e: Konva.KonvaEventObject<MouseEvent>) => {
    if (mode !== 'draw') return
    if ((e.target as Konva.Node).id().startsWith('zone-')) return
    const pos = getDocPos()
    if (!pos) return
    drawStart.current = pos
    setDrawing({ x: pos.x, y: pos.y, w: 0, h: 0 })
  }

  const handleMouseMove = () => {
    if (!drawStart.current) return
    const pos = getDocPos()
    if (!pos) return
    setDrawing({ x: drawStart.current.x, y: drawStart.current.y, w: pos.x - drawStart.current.x, h: pos.y - drawStart.current.y })
  }

  const handleMouseUp = () => {
    if (!drawStart.current || !drawing) return
    const x = Math.min(drawing.x, drawing.x + drawing.w)
    const y = Math.min(drawing.y, drawing.y + drawing.h)
    const w = Math.abs(drawing.w)
    const h = Math.abs(drawing.h)
    drawStart.current = null
    setDrawing(null)
    if (w < 5 || h < 5) return
    onZoneDrawn({
      label: `Zone ${zones.length + 1}`,
      box: rectToBox(x, y, w, h),
      respondent_id: activeRespondentId,
      field_type_id: activeFieldTypeId,
      faker_provider: 'name',
      custom_values: [],
      alignment: 'left',
    })
  }

  const activeRespondent = respondents.find(r => r.respondent_id === activeRespondentId)

  return (
    <div>
      {/* Toolbar */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', marginBottom: 8 }}>
        <button onClick={() => { setMode('draw'); onZoneSelect(null) }} style={btnStyle(mode === 'draw')}>
          Draw
        </button>
        <button onClick={() => setMode('select')} style={btnStyle(mode === 'select')}>
          Select
        </button>
        <span style={{ fontSize: 12, color: '#777', marginLeft: 4 }}>
          {mode === 'draw' ? 'Drag to draw a zone' : 'Click to select · drag to move · handles to resize'}
        </span>
        <span style={{ marginLeft: 'auto', fontSize: 12, display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Active respondent colour dot */}
          {(() => {
            const idx = respondents.findIndex(r => r.respondent_id === activeRespondentId)
            const color = getRespondentColor(idx)
            return <span style={{ width: 10, height: 10, borderRadius: '50%', background: color, display: 'inline-block' }} />
          })()}
          <select
            value={activeRespondentId}
            onChange={e => {
              setActiveRespondentId(e.target.value)
              const r = respondents.find(r => r.respondent_id === e.target.value)
              setActiveFieldTypeId(r?.field_types[0]?.field_type_id ?? 'standard')
            }}
          >
            {respondents.map(r => (
              <option key={r.respondent_id} value={r.respondent_id}>{r.display_name}</option>
            ))}
          </select>
          <select value={activeFieldTypeId} onChange={e => setActiveFieldTypeId(e.target.value)}>
            {(activeRespondent?.field_types ?? []).map(ft => (
              <option key={ft.field_type_id} value={ft.field_type_id}>{ft.display_name}</option>
            ))}
          </select>
        </span>
      </div>

      {/* Canvas */}
      <div ref={containerRef} style={{ width: '100%', border: '1px solid #ccc', lineHeight: 0 }}>
        <Stage
          ref={stageRef}
          width={stageWidth}
          height={stageHeight}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          style={{ cursor: mode === 'draw' ? 'crosshair' : 'default' }}
        >
          <Layer listening={false}>
            {bgImage && <KonvaImage image={bgImage} width={stageWidth} height={stageHeight} />}
          </Layer>

          <Layer>
            {zones.map(zone => {
              const { x, y, w, h } = boxToRect(zone.box)
              const respondentIdx = respondents.findIndex(r => r.respondent_id === zone.respondent_id)
              const color = getRespondentColor(respondentIdx)
              const isSelected = zone.zone_id === selectedId

              const respondent = respondents[respondentIdx]
              const fieldType = respondent?.field_types.find(ft => ft.field_type_id === zone.field_type_id)
                ?? respondent?.field_types[0]
              const avgFontSize = fieldType
                ? Math.round(((fieldType.font_size_range[0] + fieldType.font_size_range[1]) / 2) * displayScale)
                : 11
              const fontSize = Math.max(9, Math.min(avgFontSize, 28))
              const fontFamily = FONT_FAMILY_MAP[fieldType?.font_family ?? 'sans-serif'] ?? 'Arial'
              const fontColor = fieldType?.font_color ?? '#000000'
              const fontStyle = [fieldType?.bold ? 'bold' : '', fieldType?.italic ? 'italic' : '']
                .filter(Boolean).join(' ') || 'normal'
              const sx = x * displayScale
              const sy = y * displayScale
              const sw = w * displayScale
              const sh = h * displayScale

              const preview = zonePreviews[zone.zone_id]
              const previewText = preview?.text ?? ''
              // Mirror Python _apply_jitter: dx/dy are zone-fraction offsets sampled
              // from the same truncated Gaussian. Clamp so text stays inside zone.
              const rawTextX = sx + (preview?.dx ?? 0.05) * sw
              const rawTextY = sy + (preview?.dy ?? 0.10) * sh
              // Keep text below the label tab (≈12px) and within zone bounds
              const LABEL_H = 12
              const textX = Math.max(sx + 2, Math.min(rawTextX, sx + sw - 4))
              const textY = Math.max(sy + LABEL_H + 2, Math.min(rawTextY, sy + sh - fontSize - 2))

              return (
                <React.Fragment key={zone.zone_id}>
                  <Rect
                    id={`zone-${zone.zone_id}`}
                    ref={node => {
                      if (node) zoneRefs.current.set(zone.zone_id, node)
                      else zoneRefs.current.delete(zone.zone_id)
                    }}
                    x={sx} y={sy} width={sw} height={sh}
                    fill={color + '22'}
                    stroke={color}
                    strokeWidth={isSelected ? 2 : 1}
                    draggable={mode === 'select'}
                    onClick={e => { e.cancelBubble = true; if (mode === 'select') onZoneSelect(zone.zone_id) }}
                    onDragEnd={e => {
                      const node = e.target as Konva.Rect
                      onZoneUpdate(zone.zone_id, { box: rectToBox(node.x() / displayScale, node.y() / displayScale, w, h) })
                    }}
                    onTransformEnd={e => {
                      const node = e.target as Konva.Rect
                      const sx2 = node.scaleX(); const sy2 = node.scaleY()
                      node.scaleX(1); node.scaleY(1)
                      onZoneUpdate(zone.zone_id, {
                        box: rectToBox(node.x() / displayScale, node.y() / displayScale, (node.width() * sx2) / displayScale, (node.height() * sy2) / displayScale),
                      })
                    }}
                  />

                  {/* Zone label tab */}
                  <Text x={sx + 3} y={sy + 3} text={zone.label} fontSize={10} fill={color} fontStyle="bold" listening={false} />

                  {/* Faker preview text — position mirrors Python _apply_jitter */}
                  {previewText && (
                    <Group clipX={sx} clipY={sy + 12} clipWidth={sw} clipHeight={Math.max(0, sh - 12)} listening={false}>
                      <Text
                        x={textX}
                        y={textY}
                        text={previewText}
                        fontSize={fontSize}
                        fontFamily={fontFamily}
                        fontStyle={fontStyle}
                        fill={fontColor}
                        width={sw - 8}
                        wrap="word"
                        listening={false}
                      />
                    </Group>
                  )}
                </React.Fragment>
              )
            })}

            {/* Live drawing preview */}
            {drawing && (Math.abs(drawing.w) > 2 || Math.abs(drawing.h) > 2) && (
              <Rect
                x={Math.min(drawing.x, drawing.x + drawing.w) * displayScale}
                y={Math.min(drawing.y, drawing.y + drawing.h) * displayScale}
                width={Math.abs(drawing.w) * displayScale}
                height={Math.abs(drawing.h) * displayScale}
                fill="rgba(52,152,219,0.12)"
                stroke="#3498db"
                strokeWidth={1}
                dash={[4, 4]}
                listening={false}
              />
            )}

            <Transformer
              ref={transformerRef}
              boundBoxFunc={(oldBox, newBox) => (newBox.width < 10 || newBox.height < 10 ? oldBox : newBox)}
            />
          </Layer>
        </Stage>
      </div>
    </div>
  )
}

import React from 'react'

function btnStyle(active: boolean): React.CSSProperties {
  return {
    padding: '4px 12px', border: '1px solid #3498db', borderRadius: 4, cursor: 'pointer',
    background: active ? '#3498db' : 'white', color: active ? 'white' : '#3498db',
    fontWeight: active ? 'bold' : 'normal',
  }
}
