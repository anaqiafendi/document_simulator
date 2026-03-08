import React, { useEffect, useRef, useState } from 'react'
import Konva from 'konva'
import { Stage, Layer, Image as KonvaImage, Rect, Text, Group, Transformer } from 'react-konva'
import type { TemplateInfo, ZoneConfig, RespondentConfig } from '../types'
import type { ZonePreviewData } from '../hooks/useZonePreview'
import { getRespondentColor } from '../utils/colors'
import { fakerLabel } from '../utils/faker'

const FONT_FAMILY_MAP: Record<string, string> = {
  'sans-serif':  'Arial',
  'serif':       'Georgia',
  'monospace':   'Courier New',
  'handwriting': 'cursive',
}

// Degrees to snap to when Shift is held during rotation
const ROTATION_SNAPS = [0, 45, 90, 135, 180, 225, 270, 315]

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
  onZoneRemove: (id: string) => void
  onActiveRespondentChange?: (id: string) => void
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
  onZoneRemove,
  onActiveRespondentChange,
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
  // #4: track Shift key for rotation snapping
  const [shiftHeld, setShiftHeld] = useState(false)

  const [activeRespondentId, setActiveRespondentId] = useState(respondents[0]?.respondent_id ?? 'default')
  const [activeFieldTypeId, setActiveFieldTypeId] = useState(respondents[0]?.field_types[0]?.field_type_id ?? 'standard')

  // Notify parent of initial active respondent
  useEffect(() => {
    if (activeRespondentId && activeRespondentId !== 'default') {
      onActiveRespondentChange?.(activeRespondentId)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const displayScale = stageWidth / templateInfo.width_px
  const stageHeight = Math.round(templateInfo.height_px * displayScale)

  const setCursor = (cursor: string) => {
    if (stageRef.current) stageRef.current.container().style.cursor = cursor
  }

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

  // Show transformer for selected zone regardless of mode
  useEffect(() => {
    const tr = transformerRef.current
    if (!tr) return
    if (selectedId) {
      const node = zoneRefs.current.get(selectedId)
      tr.nodes(node ? [node] : [])
    } else {
      tr.nodes([])
    }
    tr.getLayer()?.batchDraw()
  }, [selectedId, mode, zones])

  // #4: Shift key tracking for rotation snaps
  useEffect(() => {
    const down = (e: KeyboardEvent) => { if (e.key === 'Shift') setShiftHeld(true) }
    const up = (e: KeyboardEvent) => { if (e.key === 'Shift') setShiftHeld(false) }
    window.addEventListener('keydown', down)
    window.addEventListener('keyup', up)
    return () => { window.removeEventListener('keydown', down); window.removeEventListener('keyup', up) }
  }, [])

  // #5: Delete key removes selected zone
  useEffect(() => {
    const handle = (e: KeyboardEvent) => {
      if ((e.key === 'Delete' || e.key === 'Backspace') && selectedId) {
        // Don't fire when user is typing in an input
        if (document.activeElement?.tagName === 'INPUT' || document.activeElement?.tagName === 'TEXTAREA') return
        onZoneRemove(selectedId)
        onZoneSelect(null)
      }
    }
    window.addEventListener('keydown', handle)
    return () => window.removeEventListener('keydown', handle)
  }, [selectedId, onZoneRemove, onZoneSelect])

  useEffect(() => {
    if (!respondents.find(r => r.respondent_id === activeRespondentId)) {
      const r = respondents[0]
      if (r) {
        setActiveRespondentId(r.respondent_id)
        setActiveFieldTypeId(r.field_types[0]?.field_type_id ?? 'standard')
        onActiveRespondentChange?.(r.respondent_id)
      }
    }
  }, [respondents, activeRespondentId, onActiveRespondentChange])

  const getDocPos = () => {
    const pos = stageRef.current?.getPointerPosition()
    if (!pos) return null
    return { x: pos.x / displayScale, y: pos.y / displayScale }
  }

  const handleMouseDown = (e: Konva.KonvaEventObject<MouseEvent>) => {
    if (mode !== 'draw') return
    // Don't start a draw when clicking an existing zone rect
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
    // #1: stay in Draw mode after creating a zone — user can immediately draw another
  }

  // #6: click on Stage background deselects
  const handleStageClick = (e: Konva.KonvaEventObject<MouseEvent>) => {
    if (e.target === stageRef.current) {
      onZoneSelect(null)
    }
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
          {mode === 'draw'
            ? 'Drag to draw · click zone to highlight · Del to delete selected'
            : 'Click to select · drag to move · handles to resize/rotate · Shift+rotate snaps 45°'}
        </span>
        <span style={{ marginLeft: 'auto', fontSize: 12, display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Active respondent styled selector */}
          {(() => {
            const idx = respondents.findIndex(r => r.respondent_id === activeRespondentId)
            const color = getRespondentColor(idx)
            return (
              <span style={{
                display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap',
                padding: '3px 8px',
                borderLeft: `3px solid ${color}`,
                borderRadius: 4,
                background: color + '15',
                boxShadow: `0 0 0 1px ${color}40`,
              }}>
                <span style={{ fontSize: 11, color: '#666', fontWeight: 600, whiteSpace: 'nowrap' }}>Drawing for:</span>
                <span style={{ width: 10, height: 10, borderRadius: '50%', background: color, display: 'inline-block', flexShrink: 0 }} />
                <select
                  value={activeRespondentId}
                  onChange={e => {
                    const newId = e.target.value
                    setActiveRespondentId(newId)
                    const r = respondents.find(r => r.respondent_id === newId)
                    setActiveFieldTypeId(r?.field_types[0]?.field_type_id ?? 'standard')
                    onActiveRespondentChange?.(newId)
                  }}
                  style={{ fontSize: 12, fontWeight: 600, border: `1px solid ${color}`, borderRadius: 3, outline: 'none' }}
                >
                  {respondents.map(r => (
                    <option key={r.respondent_id} value={r.respondent_id}>{r.display_name}</option>
                  ))}
                </select>
                <select value={activeFieldTypeId} onChange={e => setActiveFieldTypeId(e.target.value)}
                  style={{ fontSize: 12 }}>
                  {(activeRespondent?.field_types ?? []).map(ft => (
                    <option key={ft.field_type_id} value={ft.field_type_id}>{ft.display_name}</option>
                  ))}
                </select>
              </span>
            )
          })()}
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
          onClick={handleStageClick}
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
              // Font size is sampled once per (respondent, field_type) in useZonePreview
              // and stored in preview.fontSize (document pixels). Scale for canvas display.
              const rawFontSize = Math.round((zonePreviews[zone.zone_id]?.fontSize ?? fieldType?.font_size_range[0] ?? 12) * displayScale)
              const fontSize = Math.max(9, Math.min(rawFontSize, 32))
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
              const rawTextX = sx + (preview?.dx ?? 0.05) * sw
              const rawTextY = sy + (preview?.dy ?? 0.10) * sh
              const textX = Math.max(sx + 2, Math.min(rawTextX, sx + sw - fontSize - 2))
              const textY = Math.max(sy + 2, Math.min(rawTextY, sy + sh - fontSize - 2))

              // Floating label pill above zone
              const PILL_H = 18
              const fieldTypeName = fieldType?.display_name ?? ''
              const labelText = `${zone.label} · ${fakerLabel(zone.faker_provider)}${fieldTypeName ? ` · ${fieldTypeName}` : ''}`
              const approxTextWidth = labelText.length * 6 + 6
              const pillWidth = Math.min(Math.max(approxTextWidth, 40), Math.max(sw, 40))
              const pillY = sy < PILL_H ? sy : sy - PILL_H

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
                    draggable={true}
                    // #1: clicking a zone only highlights in sidebar — stays in Draw mode
                    onClick={e => { e.cancelBubble = true; onZoneSelect(zone.zone_id) }}
                    // #3: cursor hints on hover; selected zone uses grab/grabbing convention
                    onMouseEnter={() => {
                      if (isSelected) {
                        setCursor('grab')
                      } else {
                        setCursor(mode === 'select' ? 'move' : 'pointer')
                      }
                    }}
                    onMouseLeave={() => setCursor(mode === 'draw' ? 'crosshair' : 'default')}
                    onDragStart={() => setCursor('grabbing')}
                    onDragEnd={e => {
                      setCursor(isSelected ? 'grab' : mode === 'select' ? 'move' : 'pointer')
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

                  {/* Floating label pill above (or inside) zone */}
                  <Group x={sx} y={pillY} listening={false}>
                    <Rect x={0} y={0} width={pillWidth} height={PILL_H} fill={color} opacity={0.9} cornerRadius={3} />
                    <Text
                      x={0} y={0} width={pillWidth} height={PILL_H}
                      text={labelText} fontSize={10} fontStyle="bold" fill="white"
                      padding={3} ellipsis={true} wrap="none" listening={false}
                    />
                  </Group>

                  {/* Faker preview text */}
                  {previewText && (
                    <Group clipX={sx} clipY={sy} clipWidth={sw} clipHeight={sh} listening={false}>
                      <Text
                        x={textX} y={textY} text={previewText}
                        fontSize={fontSize} fontFamily={fontFamily} fontStyle={fontStyle}
                        fill={fontColor} width={sw - 8} wrap="word" listening={false}
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

            {/* #2 & #4: styled rotation handle + 45° snap on Shift */}
            <Transformer
              ref={transformerRef}
              boundBoxFunc={(oldBox, newBox) => (newBox.width < 10 || newBox.height < 10 ? oldBox : newBox)}
              rotationAnchorOffset={20}
              rotationAnchorFill="#fff"
              rotationAnchorStroke="#3498db"
              rotationAnchorStrokeWidth={2}
              rotationAnchorSize={12}
              rotationAnchorCursor="crosshair"
              anchorSize={9}
              anchorCornerRadius={2}
              anchorFill="#fff"
              anchorStroke="#3498db"
              anchorStrokeWidth={2}
              rotationSnaps={shiftHeld ? ROTATION_SNAPS : []}
              rotationSnapTolerance={8}
            />
          </Layer>
        </Stage>
      </div>
    </div>
  )
}

function btnStyle(active: boolean): React.CSSProperties {
  return {
    padding: '4px 12px', border: '1px solid #3498db', borderRadius: 4, cursor: 'pointer',
    background: active ? '#3498db' : 'white', color: active ? 'white' : '#3498db',
    fontWeight: active ? 'bold' : 'normal',
  }
}
