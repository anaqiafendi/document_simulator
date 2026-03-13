const PRESETS = ['#000000', '#1a3a8c', '#c0392b', '#1a6b2a', '#6c3483']

interface Props {
  value: string
  onChange: (color: string) => void
}

export default function InkColorPicker({ value, onChange }: Props) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
      {PRESETS.map(c => (
        <button
          key={c}
          title={c}
          onClick={() => onChange(c)}
          style={{
            width: 20,
            height: 20,
            background: c,
            border: value === c ? '2px solid #333' : '1px solid #aaa',
            borderRadius: 3,
            cursor: 'pointer',
            padding: 0,
          }}
        />
      ))}
      <input
        type="color"
        value={value}
        onChange={e => onChange(e.target.value)}
        style={{ width: 28, height: 24, padding: 0, border: 'none', cursor: 'pointer' }}
        title="Custom color"
      />
    </span>
  )
}
