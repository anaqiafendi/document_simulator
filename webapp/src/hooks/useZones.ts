import { useRef, useState } from 'react'
import type { ZoneConfig } from '../types'

let _counter = 0
function nextId() { return `zone_${++_counter}` }

export function useZones() {
  const [zones, setZones] = useState<ZoneConfig[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const historyRef = useRef<ZoneConfig[][]>([])

  const pushHistory = (current: ZoneConfig[]) => {
    historyRef.current = [...historyRef.current.slice(-49), current]
  }

  const addZone = (partial: Omit<ZoneConfig, 'zone_id'>) => {
    const zone: ZoneConfig = { zone_id: nextId(), ...partial }
    setZones(prev => { pushHistory(prev); return [...prev, zone] })
    setSelectedId(zone.zone_id)
    return zone
  }

  const updateZone = (zone_id: string, patch: Partial<ZoneConfig>) => {
    setZones(prev => { pushHistory(prev); return prev.map(z => z.zone_id === zone_id ? { ...z, ...patch } : z) })
  }

  const removeZone = (zone_id: string) => {
    setZones(prev => { pushHistory(prev); return prev.filter(z => z.zone_id !== zone_id) })
    setSelectedId(prev => (prev === zone_id ? null : prev))
  }

  const selectZone = (zone_id: string | null) => setSelectedId(zone_id)

  const undo = () => {
    const history = historyRef.current
    if (history.length === 0) return
    const prev = history[history.length - 1]
    historyRef.current = history.slice(0, -1)
    setZones(prev)
  }

  /** Replace all zones at once (e.g. when a template style is selected). */
  const replaceZones = (next: ZoneConfig[]) => {
    setZones(prev => { pushHistory(prev); return next })
    setSelectedId(null)
  }

  return { zones, selectedId, addZone, updateZone, removeZone, selectZone, undo, replaceZones }
}
