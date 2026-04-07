import { useRef, useState } from 'react'
import { extractSchema } from '../api/client'
import type { DocumentSchema, FieldSchema, FieldDataType, SchemaBackend } from '../types'

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
  'text', 'name', 'date', 'time', 'datetime', 'number', 'currency',
  'phone', 'email', 'address', 'company', 'id', 'checkbox', 'signature', 'other',
]

const BACKENDS: { value: SchemaBackend; label: string; note: string }[] = [
  { value: 'mock', label: 'Mock', note: 'No API key needed — returns a demo schema' },
  { value: 'openai', label: 'OpenAI GPT-4o', note: 'Requires OPENAI_API_KEY on the server' },
  { value: 'anthropic', label: 'Anthropic Claude', note: 'Requires ANTHROPIC_API_KEY on the server' },
]

const TYPE_COLORS: Record<FieldDataType, string> = {
  text: '#6b7280', name: '#7c3aed', date: '#2563eb', time: '#0891b2',
  datetime: '#0e7490', number: '#d97706', currency: '#15803d',
  phone: '#9333ea', email: '#db2777', address: '#b45309',
  company: '#4338ca', id: '#dc2626', checkbox: '#65a30d',
  signature: '#c2410c', other: '#71717a',
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

// ── Main component ────────────────────────────────────────────────────────────

export default function SchemaExtraction() {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [files, setFiles] = useState<File[]>([])
  const [previews, setPreviews] = useState<string[]>([])
  const [backend, setBackend] = useState<SchemaBackend>('mock')
  const [schema, setSchema] = useState<DocumentSchema | null>(null)
  const [editedFields, setEditedFields] = useState<FieldSchema[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [usedMessage, setUsedMessage] = useState<string | null>(null)

  // ── File handling ──────────────────────────────────────────────────────────

  const handleFilesSelected = (newFiles: FileList | null) => {
    if (!newFiles || newFiles.length === 0) return
    const accepted = Array.from(newFiles).filter(f =>
      /\.(png|jpe?g|bmp|tiff?|pdf)$/i.test(f.name)
    ).slice(0, 10)
    setFiles(accepted)
    setSchema(null)
    setEditedFields([])
    setError(null)
    setUsedMessage(null)

    // Generate object URL previews
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
    setSchema(null)
    setEditedFields([])
    setUsedMessage(null)
  }

  // ── Extraction ──────────────────────────────────────────────────────────────

  const handleExtract = async () => {
    if (files.length === 0) return
    setLoading(true)
    setError(null)
    setUsedMessage(null)
    try {
      const result = await extractSchema(files, backend)
      setSchema(result)
      setEditedFields(result.fields.map(f => ({ ...f, example_values: [...f.example_values] })))
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  // ── Field editing ──────────────────────────────────────────────────────────

  const updateField = (idx: number, patch: Partial<FieldSchema>) => {
    setEditedFields(prev => prev.map((f, i) => i === idx ? { ...f, ...patch } : f))
  }

  const updateExampleValues = (idx: number, raw: string) => {
    updateField(idx, { example_values: raw.split(',').map(v => v.trim()).filter(Boolean) })
  }

  const addField = () => {
    setEditedFields(prev => [...prev, {
      field_name: 'New Field',
      data_type: 'text',
      description: '',
      example_values: [],
      faker_provider: null,
      required: false,
    }])
  }

  const removeField = (idx: number) => {
    setEditedFields(prev => prev.filter((_, i) => i !== idx))
  }

  // ── Use Schema ─────────────────────────────────────────────────────────────

  const handleUseSchema = () => {
    const final: DocumentSchema = { ...schema!, fields: editedFields }
    console.log('[SchemaExtraction] Use Schema clicked:', final)
    setUsedMessage(
      `Schema "${final.document_type}" with ${final.fields.length} field(s) logged to console. ` +
      'Integration with the zone configurator is coming soon.'
    )
  }

  // ── Export JSON ────────────────────────────────────────────────────────────

  const handleExportJson = () => {
    if (!schema) return
    const final: DocumentSchema = { ...schema, fields: editedFields }
    const blob = new Blob([JSON.stringify(final, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `schema_${final.document_type}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px 24px' }}>
      <h2 style={{ margin: '0 0 4px', fontSize: 22 }}>Schema Extraction</h2>
      <p style={{ color: '#666', margin: '0 0 20px', fontSize: 14 }}>
        Upload 1–10 sample document scans. An LLM will identify the fields and data types present,
        producing an editable schema you can use to drive the Synthetic Generator.
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
                transition: 'border-color 0.15s',
                minHeight: 80,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                gap: 4,
              }}
            >
              <span style={{ fontSize: 24 }}>📎</span>
              <span style={{ fontSize: 13, color: '#666' }}>
                Click to browse or drag-and-drop
              </span>
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
          <div style={{ flex: '0 0 260px' }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>LLM Backend</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {BACKENDS.map(b => (
                <label
                  key={b.value}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 10,
                    padding: '10px 12px',
                    borderRadius: 6,
                    border: `1px solid ${backend === b.value ? '#4f6ef7' : '#e0e0e0'}`,
                    background: backend === b.value ? '#f0f3ff' : '#fff',
                    cursor: 'pointer',
                    transition: 'all 0.15s',
                  }}
                >
                  <input
                    type="radio"
                    name="backend"
                    value={b.value}
                    checked={backend === b.value}
                    onChange={() => setBackend(b.value)}
                    style={{ marginTop: 2 }}
                  />
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>{b.label}</div>
                    <div style={{ fontSize: 11, color: '#888', marginTop: 2 }}>{b.note}</div>
                  </div>
                </label>
              ))}
            </div>
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
                    src={url}
                    alt={files[i]?.name}
                    title={files[i]?.name}
                    style={{
                      width: 80, height: 80, objectFit: 'cover',
                      borderRadius: 6, border: '1px solid #e0e0e0',
                      display: 'block',
                    }}
                  />
                  <button
                    onClick={() => removeFile(i)}
                    title="Remove"
                    style={{
                      position: 'absolute', top: -6, right: -6,
                      width: 18, height: 18, borderRadius: '50%',
                      border: 'none', background: '#e53e3e', color: '#fff',
                      fontSize: 10, fontWeight: 700, cursor: 'pointer',
                      lineHeight: '18px', textAlign: 'center', padding: 0,
                    }}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action row */}
        <div style={{ marginTop: 16, display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            style={loading || files.length === 0 ? btnDisabled : btn}
            disabled={loading || files.length === 0}
            onClick={handleExtract}
          >
            {loading ? 'Extracting…' : 'Extract Schema'}
          </button>
          {files.length === 0 && (
            <span style={{ fontSize: 13, color: '#aaa' }}>Upload at least one image to start.</span>
          )}
        </div>

        {error && (
          <div style={{ marginTop: 12, color: '#c0392b', background: '#fdecea', padding: '8px 12px', borderRadius: 5, fontSize: 13 }}>
            {error}
          </div>
        )}
      </div>

      {/* Schema results */}
      {schema && (
        <>
          {/* Header row */}
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap', marginBottom: 12 }}>
            <div style={{ flex: 1 }}>
              <span style={{ fontSize: 14, fontWeight: 700 }}>Document type: </span>
              <input
                value={schema.document_type}
                onChange={e => setSchema({ ...schema, document_type: e.target.value })}
                style={{ ...inputCell, display: 'inline', width: 180, marginLeft: 6 }}
              />
              <span style={{ marginLeft: 12, fontSize: 12, color: '#888' }}>
                Backend: <strong>{schema.backend_used}</strong> · {editedFields.length} field(s)
              </span>
            </div>
            <button style={btnSecondary} onClick={addField}>+ Add Field</button>
            <button style={btnSecondary} onClick={handleExportJson}>Export JSON</button>
            <button style={btn} onClick={handleUseSchema}>Use Schema</button>
          </div>

          {usedMessage && (
            <div style={{ marginBottom: 12, color: '#276749', background: '#f0fff4', padding: '8px 12px', borderRadius: 5, fontSize: 13, border: '1px solid #c6f6d5' }}>
              {usedMessage}
            </div>
          )}

          {schema.notes && (
            <div style={{ marginBottom: 12, fontSize: 13, color: '#555', background: '#fffde7', padding: '8px 12px', borderRadius: 5, border: '1px solid #fff3b0' }}>
              <strong>Notes:</strong> {schema.notes}
            </div>
          )}

          {/* Editable field table */}
          <div style={{ ...card, padding: 0, overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: '#f5f5f8' }}>
                  {['Field Name', 'Type', 'Description', 'Example Values', 'Faker Provider', 'Req.', ''].map(h => (
                    <th
                      key={h}
                      style={{
                        padding: '10px 12px',
                        textAlign: 'left',
                        borderBottom: '1px solid #e0e0e0',
                        fontWeight: 600,
                        fontSize: 12,
                        color: '#555',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {editedFields.map((field, idx) => (
                  <tr
                    key={idx}
                    style={{ borderBottom: '1px solid #f0f0f0', background: idx % 2 === 0 ? '#fff' : '#fafafe' }}
                  >
                    {/* Field name */}
                    <td style={{ padding: '8px 12px', minWidth: 140 }}>
                      <input
                        value={field.field_name}
                        onChange={e => updateField(idx, { field_name: e.target.value })}
                        style={inputCell}
                      />
                    </td>

                    {/* Data type */}
                    <td style={{ padding: '8px 12px', minWidth: 130 }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        <select
                          value={field.data_type}
                          onChange={e => updateField(idx, { data_type: e.target.value as FieldDataType })}
                          style={{ ...inputCell, cursor: 'pointer' }}
                        >
                          {FIELD_DATA_TYPES.map(t => (
                            <option key={t} value={t}>{t}</option>
                          ))}
                        </select>
                        <TypeBadge type={field.data_type} />
                      </div>
                    </td>

                    {/* Description */}
                    <td style={{ padding: '8px 12px', minWidth: 180 }}>
                      <input
                        value={field.description}
                        onChange={e => updateField(idx, { description: e.target.value })}
                        placeholder="Brief description…"
                        style={inputCell}
                      />
                    </td>

                    {/* Example values */}
                    <td style={{ padding: '8px 12px', minWidth: 200 }}>
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
                            >
                              {v}
                            </span>
                          ))}
                          {field.example_values.length > 3 && (
                            <span style={{ fontSize: 11, color: '#999' }}>+{field.example_values.length - 3} more</span>
                          )}
                        </div>
                      )}
                    </td>

                    {/* Faker provider */}
                    <td style={{ padding: '8px 12px', minWidth: 160 }}>
                      <input
                        value={field.faker_provider ?? ''}
                        onChange={e => updateField(idx, { faker_provider: e.target.value || null })}
                        placeholder="e.g. name, date…"
                        style={{ ...inputCell, fontFamily: 'monospace', fontSize: 12 }}
                      />
                    </td>

                    {/* Required */}
                    <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                      <input
                        type="checkbox"
                        checked={field.required}
                        onChange={e => updateField(idx, { required: e.target.checked })}
                        style={{ width: 15, height: 15, cursor: 'pointer' }}
                      />
                    </td>

                    {/* Remove */}
                    <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                      <button
                        onClick={() => removeField(idx)}
                        title="Remove field"
                        style={{
                          background: 'none', border: 'none', cursor: 'pointer',
                          color: '#e53e3e', fontSize: 16, lineHeight: 1, padding: 2,
                        }}
                      >
                        ×
                      </button>
                    </td>
                  </tr>
                ))}

                {editedFields.length === 0 && (
                  <tr>
                    <td
                      colSpan={7}
                      style={{ padding: '20px', textAlign: 'center', color: '#bbb', fontSize: 13 }}
                    >
                      No fields. Click <strong>+ Add Field</strong> to add one manually.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Bottom action bar */}
          <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 8 }}>
            <button style={btnSecondary} onClick={addField}>+ Add Field</button>
            <button style={btnSecondary} onClick={handleExportJson}>Export JSON</button>
            <button style={btn} onClick={handleUseSchema}>Use Schema</button>
          </div>
        </>
      )}

      {!schema && !loading && files.length === 0 && (
        <div style={{ textAlign: 'center', padding: '48px 0', color: '#bbb', fontSize: 14 }}>
          Upload sample document images to extract a field schema.
        </div>
      )}

      {!schema && !loading && files.length > 0 && (
        <div style={{ textAlign: 'center', padding: '48px 0', color: '#999', fontSize: 14 }}>
          Click <strong>Extract Schema</strong> to analyse the uploaded document(s).
        </div>
      )}
    </div>
  )
}
