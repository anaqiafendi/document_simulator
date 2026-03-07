import { useState } from 'react'
import type { ZoneConfig } from '../types'

let _counter = 0
function nextId() { return `zone_${++_counter}` }

export function useZones() {
  const [zones, setZones] = useState<ZoneConfig[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const addZone = (partial: Omit<ZoneConfig, 'zone_id'>) => {
    const zone: ZoneConfig = { zone_id: nextId(), ...partial }
    setZones(prev => [...prev, zone])
    setSelectedId(zone.zone_id)
    return zone
  }

  const updateZone = (zone_id: string, patch: Partial<ZoneConfig>) => {
    setZones(prev => prev.map(z => z.zone_id === zone_id ? { ...z, ...patch } : z))
  }

  const removeZone = (zone_id: string) => {
    setZones(prev => prev.filter(z => z.zone_id !== zone_id))
    setSelectedId(prev => (prev === zone_id ? null : prev))
  }

  const selectZone = (zone_id: string | null) => setSelectedId(zone_id)

  return { zones, selectedId, addZone, updateZone, removeZone, selectZone }
}
