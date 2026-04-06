import { useEffect, useState } from 'react'

export default function StatusBar() {
  const [status, setStatus] = useState<'checking' | 'ok' | 'error'>('checking')

  useEffect(() => {
    const check = async () => {
      try {
        const r = await fetch('/health')
        setStatus(r.ok ? 'ok' : 'error')
      } catch {
        setStatus('error')
      }
    }
    check()
    const t = setInterval(check, 5000)
    return () => clearInterval(t)
  }, [])

  const color = status === 'ok' ? '#2ecc71' : status === 'error' ? '#e74c3c' : '#f39c12'
  const label = status === 'ok' ? 'API connected' : status === 'error' ? 'API unreachable' : 'Connecting...'

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#555', marginBottom: 16 }}>
      <span style={{ width: 10, height: 10, borderRadius: '50%', background: color, display: 'inline-block' }} />
      {label}
    </div>
  )
}
