import { useEffect, useMemo, useRef, useState } from 'react'
import { extractSchema, listFakerProviders } from '../api/client'
import type {
  BoundingBox,
  CurrencyInfo,
  DocumentSchema,
  FakerProvider,
  FakerProvidersResponse,
  FieldDataType,
  FieldSchema,
  LineItem,
  SchemaBackend,
  SchemaExtractionResponse,
} from '../types'

// ── Styles ────────────────────────────────────────────────────────────────────

const card: React.CSSProperties = {
  background: '#fff',
  borderRadius: 8,
  border: '1px solid #e0e0e0',
  padding: '16px 20px',
  marginBottom: 16,
}

const btn: React.CSSProperties = {
  padding: '8px 20px',
  borderRadius: 6,
  border: 'none',
  cursor: 'pointer',
  fontSize: 14,
  fontWeight: 600,
  background: '#4f6ef7',
  color: '#fff',
}

const btnDisabled: React.CSSProperties = { ...btn, background: '#aaa', cursor: 'not-allowed' }

const btnSecondary: React.CSSProperties = {
  ...btn,
  background: '#f0f0f0',
  color: '#333',
  border: '1px solid #ccc',
}

const inputCell: React.CSSProperties = {
  width: '100%',
  fontSize: 13,
  border: '1px solid #e0e0e0',
  borderRadius: 4,
  padding: '4px 8px',
  fontFamily: 'inherit',
  boxSizing: 'border-box',
}

const FIELD_DATA_TYPES: FieldDataType[] = [
  'text', 'name', 'date', 'time', 'datetime', 'number', 'amount', 'currency',
  'percentage', 'currency_code', 'language_code', 'phone', 'email', 'address',
  'company', 'id', 'checkbox', 'signature', 'line_items', 'boolean', 'other', 'unknown',
]

const BACKENDS: { value: SchemaBackend; label: string; note: string; free?: boolean; keyLabel?: string; keyPlaceholder?: string; isVertexAI?: boolean }[] = [
  { value: 'mock',       label: 'Mock',             note: 'No API key — returns a demo receipt schema. Good for testing.',                      },
  { value: 'gemini',     label: 'Gemini Flash',     note: 'Free tier via Google AI Studio (aistudio.google.com/app/apikey)', free: true,
    keyLabel: 'Google AI Studio API Key', keyPlaceholder: 'AIza…' },
  { value: 'groq',       label: 'Groq (LLaMA)',     note: 'Free tier via Groq console (console.groq.com)', free: true,
    keyLabel: 'Groq API Key', keyPlaceholder: 'gsk_…' },
  { value: 'openai',     label: 'OpenAI GPT-4o',    note: 'Paid — requires an OpenAI API key',
    keyLabel: 'OpenAI API Key', keyPlaceholder: 'sk-…' },
  { value: 'anthropic',  label: 'Anthropic Claude', note: 'Paid — requires an Anthropic API key',
    keyLabel: 'Anthropic API Key', keyPlaceholder: 'sk-ant-…' },
  { value: 'vertex_ai',  label: 'Vertex AI',        note: 'GCP Gemini — requires a service account or ADC', isVertexAI: true,
    keyLabel: 'Service Account JSON', keyPlaceholder: '{"type":"service_account",…}' },
]

const TYPE_COLORS: Record<FieldDataType, string> = {
  text: '#6b7280', name: '#7c3aed', date: '#2563eb', time: '#0891b2',
  datetime: '#0e7490', number: '#d97706', amount: '#b45309', currency: '#15803d',
  percentage: '#16a34a', currency_code: '#15803d', language_code: '#0ea5e9',
  phone: '#9333ea', email: '#db2777', address: '#b45309',
  company: '#4338ca', id: '#dc2626', checkbox: '#65a30d',
  signature: '#c2410c', line_items: '#0369a1', boolean: '#059669',
  other: '#71717a', unknown: '#71717a',
}

// ── Sub-components ────────────────────────────────────────────────────────────

function TypeBadge({ type }: { type: FieldDataType }) {
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 8px',
      borderRadius: 10,
      fontSize: 11,
      fontWeight: 600,
      background: TYPE_COLORS[type] + '18',
      color: TYPE_COLORS[type],
      border: `1px solid ${TYPE_COLORS[type]}40`,
      textTransform: 'uppercase',
      letterSpacing: '0.04em',
    }}>
      {type}
    </span>
  )
}

function Pill({ text, color, title }: { text: string; color: string; title?: string }) {
  return (
    <span
      title={title}
      style={{
        display: 'inline-block',
        padding: '1px 7px',
        borderRadius: 8,
        fontSize: 10.5,
        fontWeight: 600,
        background: color + '1a',
        color,
        border: `1px solid ${color}33`,
        marginRight: 4,
      }}
    >
      {text}
    </span>
  )
}

function FakerProviderSelect({
  value,
  onChange,
  providers,
}: {
  value: string
  onChange: (v: string) => void
  providers: FakerProvidersResponse | null
}) {
  // If providers haven't loaded yet, render a free-text input so the user
  // isn't blocked.
  if (!providers) {
    return (
      <input
        value={value}
        onChange={e => onChange(e.target.value)}
        style={{ ...inputCell, fontFamily: 'monospace', fontSize: 12 }}
      />
    )
  }

  // Native <select> with <optgroup>s for every category.
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      style={{ ...inputCell, fontFamily: 'monospace', fontSize: 12, cursor: 'pointer' }}
    >
      <option value="">— none —</option>
      {Object.entries(providers.categories).map(([category, list]) => (
        <optgroup key={category} label={category.replace(/_/g, ' ')}>
          {list.map((p: FakerProvider) => (
            <option key={p.name} value={p.name} title={p.description}>
              {p.name}
            </option>
          ))}
        </optgroup>
      ))}
      {/* Allow custom values the LLM may have invented that aren't in our catalog */}
      {value && !Object.values(providers.categories).flat().some(p => p.name === value) && (
        <option value={value}>{value} (custom)</option>
      )}
    </select>
  )
}

function BoundingBoxOverlay({
  imageUrl,
  fields,
  lineItems,
  highlightIndex,
}: {
  imageUrl: string
  fields: FieldSchema[]
  lineItems: LineItem[]
  highlightIndex: number | null
}) {
  const [nat, setNat] = useState<{ w: number; h: number } | null>(null)

  return (
    <div style={{ position: 'relative', display: 'inline-block', maxWidth: '100%' }}>
      <img
        src={imageUrl}
        alt="Document"
        onLoad={e => {
          const img = e.currentTarget
          setNat({ w: img.naturalWidth, h: img.naturalHeight })
        }}
        style={{ display: 'block', maxWidth: '100%', height: 'auto' }}
      />
      {nat && (
        <svg
          viewBox={`0 0 ${nat.w} ${nat.h}`}
          preserveAspectRatio="xMidYMid meet"
          style={{
            position: 'absolute',
            top: 0, left: 0, width: '100%', height: '100%',
            pointerEvents: 'none',
          }}
        >
          {fields.map((f, idx) => {
            if (!f.bbox) return null
            const b = f.bbox
            const x = b.x1 * nat.w
            const y = b.y1 * nat.h
            const w = Math.max(1, (b.x2 - b.x1) * nat.w)
            const h = Math.max(1, (b.y2 - b.y1) * nat.h)
            const highlighted = highlightIndex === idx
            const stroke = highlighted ? '#059669' : '#10b981'
            const strokeWidth = highlighted ? 4 : 2
            const fill = highlighted ? 'rgba(5, 150, 105, 0.18)' : 'rgba(16, 185, 129, 0.08)'
            const labelH = Math.max(14, nat.h * 0.018)
            return (
              <g key={idx}>
                <rect
                  x={x} y={y} width={w} height={h}
                  fill={fill} stroke={stroke} strokeWidth={strokeWidth}
                  rx={3} ry={3}
                />
                {/* Field-name label above the box (or below if near top edge) */}
                <g transform={`translate(${x}, ${y > labelH * 1.5 ? y - labelH - 2 : y + h + 2})`}>
                  <rect
                    x={0} y={0}
                    width={Math.min(f.field_name.length * labelH * 0.55 + 12, nat.w - x)}
                    height={labelH}
                    fill={stroke} rx={2} ry={2}
                  />
                  <text
                    x={6} y={labelH * 0.72}
                    fontFamily="system-ui, -apple-system, sans-serif"
                    fontSize={labelH * 0.65}
                    fill="#fff" fontWeight={600}
                  >
                    {f.field_name}
                  </text>
                </g>
              </g>
            )
          })}
          {/* Line item boxes in a distinct color */}
          {lineItems.map((li, idx) => {
            if (!li.bbox) return null
            const b = li.bbox
            return (
              <rect
                key={`li-${idx}`}
                x={b.x1 * nat.w} y={b.y1 * nat.h}
                width={Math.max(1, (b.x2 - b.x1) * nat.w)}
                height={Math.max(1, (b.y2 - b.y1) * nat.h)}
                fill="rgba(59, 130, 246, 0.08)"
                stroke="#3b82f6"
                strokeWidth={1.5}
                strokeDasharray="4 3"
                rx={2} ry={2}
              />
            )
          })}
        </svg>
      )}
    </div>
  )
}

function PreviewModal({
  imageUrl,
  schema,
  onClose,
  highlightIndex,
}: {
  imageUrl: string
  schema: DocumentSchema
  onClose: () => void
  highlightIndex: number | null
}) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.82)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        zIndex: 1000, padding: 24,
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: '#fff', borderRadius: 10, maxWidth: '92vw', maxHeight: '92vh',
          overflow: 'auto', padding: 16,
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.3)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 12, gap: 12 }}>
          <strong style={{ fontSize: 14 }}>
            Image {schema.source_image_index + 1} · {schema.document_type}
          </strong>
          <span style={{ color: '#6b7280', fontSize: 12 }}>
            {schema.fields.length} fields · {schema.line_items.length} line items ·
            {schema.source_image_width && schema.source_image_height
              ? ` ${schema.source_image_width}×${schema.source_image_height}px`
              : ''}
          </span>
          <div style={{ flex: 1 }} />
          <button style={btnSecondary} onClick={onClose}>Close (Esc)</button>
        </div>
        <BoundingBoxOverlay
          imageUrl={imageUrl}
          fields={schema.fields}
          lineItems={schema.line_items}
          highlightIndex={highlightIndex}
        />
        <div style={{ marginTop: 10, display: 'flex', gap: 14, fontSize: 12, color: '#4b5563' }}>
          <span><span style={{ color: '#10b981', fontWeight: 700 }}>■</span> Fields (green)</span>
          <span><span style={{ color: '#3b82f6', fontWeight: 700 }}>▢</span> Line items (blue, dashed)</span>
        </div>
      </div>
    </div>
  )
}

function LineItemsTable({ items }: { items: LineItem[] }) {
  if (items.length === 0) return null
  return (
    <div style={{ ...card, padding: 0, overflowX: 'auto' }}>
      <div style={{ padding: '10px 14px', borderBottom: '1px solid #eef0f3', fontWeight: 700, fontSize: 13 }}>
        Line items <span style={{ color: '#999', fontWeight: 400 }}>({items.length})</span>
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr style={{ background: '#f8fafc' }}>
            {['Description', 'Qty', 'Unit price', 'Total', 'Currency', 'Language'].map(h => (
              <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontSize: 11, color: '#555', borderBottom: '1px solid #e0e0e0' }}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((li, idx) => (
            <tr key={idx} style={{ borderBottom: '1px solid #f0f0f0', background: idx % 2 === 0 ? '#fff' : '#fafafe' }}>
              <td style={{ padding: '6px 12px' }}>{li.description || <em style={{ color: '#aaa' }}>—</em>}</td>
              <td style={{ padding: '6px 12px' }}>{li.quantity ?? '—'}</td>
              <td style={{ padding: '6px 12px', fontFamily: 'monospace' }}>{li.unit_price || '—'}</td>
              <td style={{ padding: '6px 12px', fontFamily: 'monospace' }}>{li.total || '—'}</td>
              <td style={{ padding: '6px 12px' }}>{li.currency ? <Pill text={li.currency} color="#15803d" title="ISO 4217" /> : '—'}</td>
              <td style={{ padding: '6px 12px' }}>{li.language ? <Pill text={li.language} color="#2563eb" title="BCP-47" /> : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export default function SchemaExtraction() {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [files, setFiles] = useState<File[]>([])
  const [previews, setPreviews] = useState<string[]>([])
  const [backend, setBackend] = useState<SchemaBackend>('gemini')
  const [apiKey, setApiKey] = useState('')
  const [serviceAccountJson, setServiceAccountJson] = useState('')

  // Per-image results — one schema + one source-image b64 per uploaded image.
  const [schemas, setSchemas] = useState<DocumentSchema[]>([])
  const [sourceImages, setSourceImages] = useState<string[]>([])
  const [activeTab, setActiveTab] = useState(0)

  // Editing surface: parallel to `schemas` so edits are kept per-image.
  const [editedFields, setEditedFields] = useState<FieldSchema[][]>([])

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [usedMessage, setUsedMessage] = useState<string | null>(null)

  // Faker provider catalogue (loaded once on mount).
  const [providers, setProviders] = useState<FakerProvidersResponse | null>(null)
  const [currencies, setCurrencies] = useState<CurrencyInfo[]>([])

  // Preview modal state
  const [modalIndex, setModalIndex] = useState<number | null>(null)
  const [hoveredFieldIdx, setHoveredFieldIdx] = useState<number | null>(null)

  useEffect(() => {
    listFakerProviders()
      .then(r => {
        setProviders(r)
        setCurrencies(r.currencies)
      })
      .catch(err => {
        console.warn('Could not load faker providers:', err)
      })
  }, [])

  const activeSchema: DocumentSchema | null = schemas[activeTab] ?? null
  const activeFields: FieldSchema[] = editedFields[activeTab] ?? []

  // ── File handling ──────────────────────────────────────────────────────────

  const handleFilesSelected = (newFiles: FileList | null) => {
    if (!newFiles || newFiles.length === 0) return
    const accepted = Array.from(newFiles).filter(f =>
      /\.(png|jpe?g|bmp|tiff?|pdf)$/i.test(f.name)
    ).slice(0, 10)
    setFiles(accepted)
    setSchemas([])
    setSourceImages([])
    setEditedFields([])
    setActiveTab(0)
    setError(null)
    setUsedMessage(null)

    const urls = accepted.map(f => URL.createObjectURL(f))
    setPreviews(prev => {
      prev.forEach(u => URL.revokeObjectURL(u))
      return urls
    })
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    handleFilesSelected(e.dataTransfer.files)
  }

  const removeFile = (idx: number) => {
    URL.revokeObjectURL(previews[idx])
    setFiles(f => f.filter((_, i) => i !== idx))
    setPreviews(p => p.filter((_, i) => i !== idx))
    setSchemas([])
    setSourceImages([])
    setEditedFields([])
    setActiveTab(0)
    setUsedMessage(null)
  }

  // ── Extraction ──────────────────────────────────────────────────────────────

  const handleExtract = async () => {
    if (files.length === 0) return
    setLoading(true)
    setError(null)
    setUsedMessage(null)
    try {
      const result: SchemaExtractionResponse = await extractSchema(
        files,
        backend,
        apiKey || undefined,
        serviceAccountJson || undefined,
      )
      setSchemas(result.schemas)
      setSourceImages(result.source_images)
      setEditedFields(
        result.schemas.map(s =>
          s.fields.map(f => ({ ...f, example_values: [...f.example_values] }))
        )
      )
      setActiveTab(0)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  // ── Field editing ──────────────────────────────────────────────────────────

  const updateField = (fieldIdx: number, patch: Partial<FieldSchema>) => {
    setEditedFields(prev =>
      prev.map((fields, ti) => ti === activeTab
        ? fields.map((f, i) => i === fieldIdx ? { ...f, ...patch } : f)
        : fields
      )
    )
  }

  const updateExampleValues = (fieldIdx: number, raw: string) => {
    updateField(fieldIdx, { example_values: raw.split(',').map(v => v.trim()).filter(Boolean) })
  }

  const addField = () => {
    const newField: FieldSchema = {
      field_name: 'new_field',
      display_label: '',
      data_type: 'text',
      required: false,
      example_values: [],
      value_pattern: null,
      faker_provider: 'word',
      description: '',
      notes: '',
      bbox: null,
      language: null,
      currency: null,
    }
    setEditedFields(prev =>
      prev.map((fields, ti) => ti === activeTab ? [...fields, newField] : fields)
    )
  }

  const removeField = (fieldIdx: number) => {
    setEditedFields(prev =>
      prev.map((fields, ti) => ti === activeTab ? fields.filter((_, i) => i !== fieldIdx) : fields)
    )
  }

  // ── Use / export ───────────────────────────────────────────────────────────

  const buildFinalSchemas = (): DocumentSchema[] =>
    schemas.map((s, i) => ({ ...s, fields: editedFields[i] ?? s.fields }))

  const handleUseSchema = () => {
    const finals = buildFinalSchemas()
    console.log('[SchemaExtraction] Use Schema clicked:', finals)
    setUsedMessage(
      `${finals.length} schema(s) logged to console (${finals.reduce((acc, s) => acc + s.fields.length, 0)} fields total). ` +
      'Integration with the zone configurator is coming soon.'
    )
  }

  const handleExportJson = () => {
    const payload = { schemas: buildFinalSchemas() }
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `schemas_${files.length}_images.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  // ── Rendering helpers ──────────────────────────────────────────────────────

  const bboxSummary = (bb: BoundingBox | null): string => {
    if (!bb) return '—'
    const pct = (n: number) => `${(n * 100).toFixed(0)}%`
    return `${pct(bb.x1)},${pct(bb.y1)} → ${pct(bb.x2)},${pct(bb.y2)}`
  }

  const currencyOptions = useMemo(
    () => ['', ...currencies.map(c => c.code)],
    [currencies]
  )

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: '24px 24px' }}>
      <h2 style={{ margin: '0 0 4px', fontSize: 22 }}>Schema Extraction</h2>
      <p style={{ color: '#666', margin: '0 0 20px', fontSize: 14 }}>
        Upload 1–10 sample document scans. Each image is analysed individually so you can review
        field schemas, bounding-box overlays, line items, and detected language / currency per scan.
      </p>

      {/* Upload + config card */}
      <div style={card}>
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', alignItems: 'flex-start' }}>
          {/* Dropzone */}
          <div style={{ flex: '1 1 280px' }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>
              Sample images / PDFs <span style={{ color: '#999', fontWeight: 400 }}>(up to 10)</span>
            </div>
            <div
              onClick={() => fileInputRef.current?.click()}
              onDrop={handleDrop}
              onDragOver={e => e.preventDefault()}
              style={{
                border: '2px dashed #d0d0e0',
                borderRadius: 8,
                padding: '20px 16px',
                textAlign: 'center',
                cursor: 'pointer',
                background: '#fafafe',
                minHeight: 80,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                gap: 4,
              }}
            >
              <span style={{ fontSize: 24 }}>📎</span>
              <span style={{ fontSize: 13, color: '#666' }}>Click to browse or drag-and-drop</span>
              <span style={{ fontSize: 11, color: '#aaa' }}>PNG, JPG, TIFF, PDF</span>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".png,.jpg,.jpeg,.bmp,.tiff,.tif,.pdf"
              style={{ display: 'none' }}
              onChange={e => handleFilesSelected(e.target.files)}
            />
          </div>

          {/* Backend selector */}
          <div style={{ flex: '0 0 280px' }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>LLM Backend</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {BACKENDS.map(b => (
                <label
                  key={b.value}
                  style={{
                    display: 'flex', alignItems: 'flex-start', gap: 10,
                    padding: '8px 12px', borderRadius: 6,
                    border: `1px solid ${backend === b.value ? '#4f6ef7' : '#e0e0e0'}`,
                    background: backend === b.value ? '#f0f3ff' : '#fff',
                    cursor: 'pointer',
                  }}
                >
                  <input
                    type="radio"
                    name="backend"
                    value={b.value}
                    checked={backend === b.value}
                    onChange={() => { setBackend(b.value); setApiKey(''); setServiceAccountJson('') }}
                    style={{ marginTop: 2 }}
                  />
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>
                      {b.label}
                      {b.free && (
                        <span style={{ marginLeft: 6, fontSize: 10, fontWeight: 700, color: '#15803d', background: '#dcfce7', borderRadius: 4, padding: '1px 6px', border: '1px solid #bbf7d0' }}>
                          FREE
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: 11, color: '#888', marginTop: 2 }}>{b.note}</div>
                  </div>
                </label>
              ))}
            </div>

            {backend !== 'mock' && (() => {
              const active = BACKENDS.find(b => b.value === backend)!
              return (
                <div style={{ marginTop: 12 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4, color: '#555' }}>
                    {active.keyLabel ?? 'API Key'}
                    <span style={{ fontWeight: 400, color: '#aaa', marginLeft: 4 }}>(per request, never stored)</span>
                  </div>
                  {active.isVertexAI ? (
                    <textarea
                      rows={4}
                      value={serviceAccountJson}
                      onChange={e => setServiceAccountJson(e.target.value)}
                      placeholder={active.keyPlaceholder}
                      style={{ ...inputCell, fontFamily: 'monospace', fontSize: 11, resize: 'vertical' }}
                    />
                  ) : (
                    <input
                      type="password"
                      value={apiKey}
                      onChange={e => setApiKey(e.target.value)}
                      placeholder={active.keyPlaceholder ?? 'Paste API key…'}
                      autoComplete="off"
                      style={inputCell}
                    />
                  )}
                  {active.free && (
                    <div style={{ fontSize: 11, color: '#15803d', marginTop: 4 }}>
                      Free tier available — no credit card required.
                    </div>
                  )}
                </div>
              )
            })()}
          </div>
        </div>

        {/* Thumbnails */}
        {previews.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: '#888', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Selected ({previews.length} / 10)
            </div>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              {previews.map((url, i) => (
                <div key={i} style={{ position: 'relative' }}>
                  <img
                    src={url} alt={files[i]?.name} title={files[i]?.name}
                    style={{ width: 80, height: 80, objectFit: 'cover', borderRadius: 6, border: '1px solid #e0e0e0', display: 'block' }}
                  />
                  <button
                    onClick={() => removeFile(i)} title="Remove"
                    style={{
                      position: 'absolute', top: -6, right: -6,
                      width: 18, height: 18, borderRadius: '50%',
                      border: 'none', background: '#e53e3e', color: '#fff',
                      fontSize: 10, fontWeight: 700, cursor: 'pointer',
                      lineHeight: '18px', padding: 0,
                    }}
                  >×</button>
                </div>
              ))}
            </div>
          </div>
        )}

        <div style={{ marginTop: 16, display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            style={loading || files.length === 0 ? btnDisabled : btn}
            disabled={loading || files.length === 0}
            onClick={handleExtract}
          >
            {loading ? 'Extracting…' : `Extract ${files.length > 1 ? `${files.length} Schemas` : 'Schema'}`}
          </button>
          {files.length === 0 && (
            <span style={{ fontSize: 13, color: '#aaa' }}>Upload at least one image to start.</span>
          )}
          {files.length > 1 && (
            <span style={{ fontSize: 12, color: '#6b7280' }}>
              Each image is analysed independently — you'll get {files.length} separate schemas.
            </span>
          )}
        </div>

        {error && (
          <div style={{ marginTop: 12, color: '#c0392b', background: '#fdecea', padding: '8px 12px', borderRadius: 5, fontSize: 13 }}>
            {error}
          </div>
        )}
      </div>

      {/* Per-image tabs + schema */}
      {schemas.length > 0 && activeSchema && (
        <>
          {/* Tabs */}
          <div style={{ display: 'flex', gap: 8, borderBottom: '1px solid #e5e7eb', marginBottom: 16, flexWrap: 'wrap' }}>
            {schemas.map((s, i) => (
              <button
                key={i}
                onClick={() => setActiveTab(i)}
                style={{
                  padding: '10px 14px',
                  border: 'none',
                  borderBottom: activeTab === i ? '3px solid #4f6ef7' : '3px solid transparent',
                  background: 'transparent',
                  cursor: 'pointer',
                  fontWeight: activeTab === i ? 700 : 500,
                  color: activeTab === i ? '#1f2937' : '#6b7280',
                  fontSize: 13,
                  display: 'flex', alignItems: 'center', gap: 8,
                }}
              >
                {sourceImages[i] && (
                  <img
                    src={`data:image/png;base64,${sourceImages[i]}`}
                    alt=""
                    style={{ width: 22, height: 22, objectFit: 'cover', borderRadius: 3, border: '1px solid #e5e7eb' }}
                  />
                )}
                Image {i + 1}
                <span style={{ fontSize: 11, color: '#9ca3af', fontWeight: 500 }}>
                  ({s.fields.length}f{s.line_items.length > 0 ? ` · ${s.line_items.length}li` : ''})
                </span>
              </button>
            ))}
          </div>

          {/* Active schema — image preview (left) + fields (right) */}
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 12 }}>
            {/* Image preview */}
            {sourceImages[activeTab] && (
              <div
                style={{
                  flex: '0 0 260px',
                  ...card,
                  margin: 0,
                  padding: 10,
                  cursor: 'zoom-in',
                }}
                onClick={() => setModalIndex(activeTab)}
                title="Click to view full-size with bounding boxes"
              >
                <div style={{ position: 'relative' }}>
                  <BoundingBoxOverlay
                    imageUrl={`data:image/png;base64,${sourceImages[activeTab]}`}
                    fields={activeFields}
                    lineItems={activeSchema.line_items}
                    highlightIndex={hoveredFieldIdx}
                  />
                </div>
                <div style={{ marginTop: 8, fontSize: 11, color: '#6b7280', textAlign: 'center' }}>
                  Click to enlarge · {activeFields.filter(f => f.bbox).length} / {activeFields.length} fields located
                </div>
              </div>
            )}

            {/* Schema summary + header */}
            <div style={{ flex: 1, minWidth: 280 }}>
              <div style={{ ...card, marginBottom: 8 }}>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, alignItems: 'center' }}>
                  <span style={{ fontSize: 14, fontWeight: 700 }}>Document type:</span>
                  <input
                    value={activeSchema.document_type}
                    onChange={e => setSchemas(prev => prev.map((s, i) => i === activeTab ? { ...s, document_type: e.target.value } : s))}
                    style={{ ...inputCell, display: 'inline-block', width: 180 }}
                  />
                  <Pill text={activeSchema.language || 'en'} color="#2563eb" title="Primary language (BCP-47)" />
                  <Pill text={activeSchema.currency || 'USD'} color="#15803d" title="Primary currency (ISO 4217)" />
                  <span style={{ fontSize: 11, color: '#6b7280' }}>
                    backend: <strong>{activeSchema.backend_used || activeSchema.extractor_model}</strong>
                  </span>
                  <span style={{ fontSize: 11, color: '#6b7280' }}>
                    confidence: <strong>{(activeSchema.confidence * 100).toFixed(0)}%</strong>
                  </span>
                </div>
                {activeSchema.notes && (
                  <div style={{ marginTop: 10, fontSize: 12, color: '#555', background: '#fffde7', padding: '6px 10px', borderRadius: 4, border: '1px solid #fff3b0' }}>
                    {activeSchema.notes}
                  </div>
                )}
              </div>

              {/* Action row */}
              <div style={{ display: 'flex', gap: 8, marginBottom: 8, flexWrap: 'wrap' }}>
                <button style={btnSecondary} onClick={addField}>+ Add Field</button>
                <button style={btnSecondary} onClick={handleExportJson}>Export JSON</button>
                <button style={btn} onClick={handleUseSchema}>Use Schemas</button>
              </div>
              {usedMessage && (
                <div style={{ color: '#276749', background: '#f0fff4', padding: '8px 12px', borderRadius: 5, fontSize: 13, border: '1px solid #c6f6d5', marginBottom: 8 }}>
                  {usedMessage}
                </div>
              )}
            </div>
          </div>

          {/* Editable field table */}
          <div style={{ ...card, padding: 0, overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: '#f5f5f8' }}>
                  {['Field Name', 'Type', 'Language', 'Currency', 'Faker Provider', 'Examples', 'BBox', 'Req.', ''].map(h => (
                    <th
                      key={h}
                      style={{
                        padding: '10px 12px', textAlign: 'left', borderBottom: '1px solid #e0e0e0',
                        fontWeight: 600, fontSize: 12, color: '#555', whiteSpace: 'nowrap',
                      }}
                    >{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {activeFields.map((field, idx) => (
                  <tr
                    key={idx}
                    onMouseEnter={() => setHoveredFieldIdx(idx)}
                    onMouseLeave={() => setHoveredFieldIdx(null)}
                    style={{
                      borderBottom: '1px solid #f0f0f0',
                      background: hoveredFieldIdx === idx
                        ? '#eef6ff'
                        : (idx % 2 === 0 ? '#fff' : '#fafafe'),
                      transition: 'background 0.1s',
                    }}
                  >
                    <td style={{ padding: '8px 12px', minWidth: 140 }}>
                      <input
                        value={field.field_name}
                        onChange={e => updateField(idx, { field_name: e.target.value })}
                        style={inputCell}
                      />
                    </td>

                    <td style={{ padding: '8px 12px', minWidth: 130 }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        <select
                          value={field.data_type}
                          onChange={e => updateField(idx, { data_type: e.target.value as FieldDataType })}
                          style={{ ...inputCell, cursor: 'pointer' }}
                        >
                          {FIELD_DATA_TYPES.map(t => (<option key={t} value={t}>{t}</option>))}
                        </select>
                        <TypeBadge type={field.data_type} />
                      </div>
                    </td>

                    {/* Language */}
                    <td style={{ padding: '8px 12px', minWidth: 90 }}>
                      <input
                        value={field.language ?? ''}
                        onChange={e => updateField(idx, { language: e.target.value || null })}
                        placeholder="en"
                        style={{ ...inputCell, fontFamily: 'monospace', fontSize: 12 }}
                      />
                    </td>

                    {/* Currency */}
                    <td style={{ padding: '8px 12px', minWidth: 90 }}>
                      <select
                        value={field.currency ?? ''}
                        onChange={e => updateField(idx, { currency: e.target.value || null })}
                        style={{ ...inputCell, cursor: 'pointer', fontFamily: 'monospace', fontSize: 12 }}
                      >
                        {currencyOptions.map(c => (
                          <option key={c || '__none'} value={c}>{c || '—'}</option>
                        ))}
                      </select>
                    </td>

                    {/* Faker provider dropdown */}
                    <td style={{ padding: '8px 12px', minWidth: 170 }}>
                      <FakerProviderSelect
                        value={field.faker_provider}
                        onChange={v => updateField(idx, { faker_provider: v })}
                        providers={providers}
                      />
                    </td>

                    {/* Example values */}
                    <td style={{ padding: '8px 12px', minWidth: 180 }}>
                      <input
                        value={field.example_values.join(', ')}
                        onChange={e => updateExampleValues(idx, e.target.value)}
                        placeholder="Comma-separated…"
                        style={inputCell}
                      />
                      {field.example_values.length > 0 && (
                        <div style={{ marginTop: 4, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                          {field.example_values.slice(0, 3).map((v, vi) => (
                            <span
                              key={vi}
                              style={{
                                fontSize: 11, padding: '1px 6px', borderRadius: 4,
                                background: '#e8eaf6', color: '#3949ab', fontFamily: 'monospace',
                              }}
                            >{v}</span>
                          ))}
                          {field.example_values.length > 3 && (
                            <span style={{ fontSize: 11, color: '#999' }}>+{field.example_values.length - 3} more</span>
                          )}
                        </div>
                      )}
                    </td>

                    {/* BBox indicator */}
                    <td style={{ padding: '8px 12px', minWidth: 120, fontSize: 11, color: '#6b7280', fontFamily: 'monospace' }}>
                      {field.bbox ? (
                        <span title={bboxSummary(field.bbox)} style={{ color: '#15803d' }}>
                          ✓ {bboxSummary(field.bbox)}
                        </span>
                      ) : (
                        <span style={{ color: '#cbd5e1' }}>—</span>
                      )}
                    </td>

                    <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                      <input
                        type="checkbox"
                        checked={field.required}
                        onChange={e => updateField(idx, { required: e.target.checked })}
                        style={{ width: 15, height: 15, cursor: 'pointer' }}
                      />
                    </td>

                    <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                      <button
                        onClick={() => removeField(idx)} title="Remove field"
                        style={{
                          background: 'none', border: 'none', cursor: 'pointer',
                          color: '#e53e3e', fontSize: 16, lineHeight: 1, padding: 2,
                        }}
                      >×</button>
                    </td>
                  </tr>
                ))}
                {activeFields.length === 0 && (
                  <tr>
                    <td colSpan={9} style={{ padding: 20, textAlign: 'center', color: '#bbb', fontSize: 13 }}>
                      No fields. Click <strong>+ Add Field</strong> to add one manually.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Line items */}
          <LineItemsTable items={activeSchema.line_items} />
        </>
      )}

      {/* Preview modal */}
      {modalIndex !== null && schemas[modalIndex] && sourceImages[modalIndex] && (
        <PreviewModal
          imageUrl={`data:image/png;base64,${sourceImages[modalIndex]}`}
          schema={{ ...schemas[modalIndex], fields: editedFields[modalIndex] ?? schemas[modalIndex].fields }}
          onClose={() => setModalIndex(null)}
          highlightIndex={hoveredFieldIdx}
        />
      )}

      {schemas.length === 0 && !loading && files.length === 0 && (
        <div style={{ textAlign: 'center', padding: '48px 0', color: '#bbb', fontSize: 14 }}>
          Upload sample document images to extract a field schema per image.
        </div>
      )}
      {schemas.length === 0 && !loading && files.length > 0 && (
        <div style={{ textAlign: 'center', padding: '48px 0', color: '#999', fontSize: 14 }}>
          Click <strong>Extract Schema</strong> to analyse the uploaded document(s).
        </div>
      )}
    </div>
  )
}
