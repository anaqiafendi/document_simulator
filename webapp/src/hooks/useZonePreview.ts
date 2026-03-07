import { useCallback, useState } from 'react'
import type { ZoneConfig } from '../types'
import { generateFakerValue } from '../utils/faker'

export interface ZonePreviewData {
  text: string
  /** x offset as fraction of zone width  (mirrors Python _apply_jitter mean_x logic) */
  dx: number
  /** y offset as fraction of zone height (mirrors Python _apply_jitter mean_y logic) */
  dy: number
}

// Box-Muller transform — matches Python's random.gauss() distribution
function gaussRandom(): number {
  let u = 0, v = 0
  while (u === 0) u = Math.random()
  while (v === 0) v = Math.random()
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v)
}

/**
 * Sample a position fraction in [0, 1], matching Python's _apply_jitter logic:
 *   jitter=0  → return defaultFraction (fixed offset, no randomness)
 *   jitter>0  → truncated Gaussian(mean=meanFraction, sigma=jitter), up to 20 retries
 */
function sampleFraction(jitter: number, meanFraction: number, defaultFraction: number): number {
  if (jitter <= 0) return defaultFraction
  for (let i = 0; i < 20; i++) {
    const v = meanFraction + jitter * gaussRandom()
    if (v >= 0 && v <= 1) return v
  }
  return meanFraction // Python's fallback
}

function makePreview(provider: string, jitter_x: number, jitter_y: number): ZonePreviewData {
  return {
    text: generateFakerValue(provider),
    // Python: jitter_x=0 → x1 + 0.05*w; jitter_x>0 → Gaussian(mean=0.12, σ=jitter_x)
    dx: sampleFraction(jitter_x, 0.12, 0.05),
    // Python: jitter_y=0 → y1 + 0.10*h; jitter_y>0 → Gaussian(mean=0.50, σ=jitter_y)
    dy: sampleFraction(jitter_y, 0.50, 0.10),
  }
}

export function useZonePreview() {
  const [previews, setPreviews] = useState<Record<string, ZonePreviewData>>({})

  const initZone = useCallback((zone: ZoneConfig, jitter_x = 0, jitter_y = 0) => {
    setPreviews(prev => ({ ...prev, [zone.zone_id]: makePreview(zone.faker_provider, jitter_x, jitter_y) }))
  }, [])

  const rerollZone = useCallback((zone_id: string, provider: string, jitter_x = 0, jitter_y = 0) => {
    setPreviews(prev => ({ ...prev, [zone_id]: makePreview(provider, jitter_x, jitter_y) }))
  }, [])

  const removeZone = useCallback((zone_id: string) => {
    setPreviews(prev => {
      const next = { ...prev }
      delete next[zone_id]
      return next
    })
  }, [])

  return { previews, initZone, rerollZone, removeZone }
}
