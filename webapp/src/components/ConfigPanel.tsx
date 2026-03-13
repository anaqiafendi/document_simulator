import { useRef } from 'react'
import type { SynthesisConfig } from '../types'

interface Props {
  config: SynthesisConfig
  onLoad: (config: SynthesisConfig) => void
}

export default function ConfigPanel({ config, onLoad }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)

  const handleSave = () => {
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'synthesis_config.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleLoad = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = ev => {
      try {
        const parsed = JSON.parse(ev.target?.result as string) as SynthesisConfig
        onLoad(parsed)
      } catch {
        alert('Invalid JSON config file')
      }
    }
    reader.readAsText(file)
    e.target.value = ''
  }

  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
      <button onClick={handleSave} style={{ fontSize: 12 }}>
        Save config JSON
      </button>
      <button onClick={() => inputRef.current?.click()} style={{ fontSize: 12 }}>
        Load config JSON
      </button>
      <input ref={inputRef} type="file" accept=".json" onChange={handleLoad} style={{ display: 'none' }} />
    </div>
  )
}
