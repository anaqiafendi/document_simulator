import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

export const FONT_OPTIONS: { key: string; label: string; css: string }[] = [
  { key: 'sans-serif',  label: 'Sans-serif',  css: 'system-ui, Arial, sans-serif' },
  { key: 'serif',       label: 'Serif',        css: 'Georgia, "Times New Roman", serif' },
  { key: 'monospace',   label: 'Monospace',    css: '"Courier New", Courier, monospace' },
  { key: 'handwriting', label: 'Handwriting',  css: 'cursive' },
]

interface Props {
  value: string
  onChange: (v: string) => void
}

export default function FontSelect({ value, onChange }: Props) {
  const [open, setOpen] = useState(false)
  const [pos, setPos] = useState({ top: 0, left: 0, width: 0 })
  const triggerRef = useRef<HTMLDivElement>(null)

  const selected = FONT_OPTIONS.find(f => f.key === value) ?? FONT_OPTIONS[0]

  const handleToggle = () => {
    if (!open && triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect()
      setPos({ top: rect.bottom, left: rect.left, width: rect.width })
    }
    setOpen(o => !o)
  }

  // Close on outside click, scroll, or resize
  useEffect(() => {
    if (!open) return
    const close = (e: Event) => {
      if (triggerRef.current && e instanceof MouseEvent && triggerRef.current.contains(e.target as Node)) return
      setOpen(false)
    }
    document.addEventListener('mousedown', close)
    window.addEventListener('scroll', close, true)
    window.addEventListener('resize', close)
    return () => {
      document.removeEventListener('mousedown', close)
      window.removeEventListener('scroll', close, true)
      window.removeEventListener('resize', close)
    }
  }, [open])

  return (
    <>
      {/* Trigger */}
      <div
        ref={triggerRef}
        onClick={handleToggle}
        style={{
          border: `1px solid ${open ? '#3498db' : '#ccc'}`,
          borderRadius: 3,
          padding: '3px 28px 3px 8px',
          cursor: 'pointer',
          fontFamily: selected.css,
          fontSize: 13,
          background: 'white',
          minWidth: 140,
          userSelect: 'none',
          position: 'relative',
          whiteSpace: 'nowrap',
          display: 'inline-block',
        }}
      >
        {selected.label}
        <span style={{ position: 'absolute', right: 7, top: '50%', transform: 'translateY(-50%)', fontSize: 9, color: '#888' }}>
          {open ? '▲' : '▼'}
        </span>
      </div>

      {/* Portal dropdown — renders at document.body so overflow:auto can't clip it */}
      {open && createPortal(
        <div
          style={{
            position: 'fixed',
            top: pos.top + 2,
            left: pos.left,
            zIndex: 99999,
            background: 'white',
            border: '1px solid #ddd',
            borderRadius: 4,
            boxShadow: '0 8px 24px rgba(0,0,0,0.16)',
            minWidth: Math.max(pos.width, 220),
          }}
        >
          {FONT_OPTIONS.map(f => (
            <div
              key={f.key}
              onMouseDown={e => {
                e.preventDefault() // prevent blur before click
                onChange(f.key)
                setOpen(false)
              }}
              style={{
                padding: '10px 14px',
                cursor: 'pointer',
                borderBottom: '1px solid #f2f2f2',
                background: value === f.key ? '#eef4ff' : 'white',
              }}
              onMouseEnter={e => { if (value !== f.key) (e.currentTarget as HTMLDivElement).style.background = '#f7f7f7' }}
              onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.background = value === f.key ? '#eef4ff' : 'white' }}
            >
              <div style={{ fontSize: 11, color: '#aaa', marginBottom: 3, fontFamily: 'system-ui' }}>
                {f.label}
              </div>
              <div style={{ fontFamily: f.css, fontSize: 15, color: '#222' }}>
                The quick brown fox
              </div>
            </div>
          ))}
        </div>,
        document.body
      )}
    </>
  )
}
