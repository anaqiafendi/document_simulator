import { useCallback, useRef, useState } from 'react'
import type { ZoneConfig } from '../types'
import { generateFakerValue } from '../utils/faker'

export interface ZonePreviewData {
  text: string
  /** x offset as fraction of zone width  (mirrors Python _apply_jitter mean_x logic) */
  dx: number
  /** y offset as fraction of zone height (mirrors Python _apply_jitter mean_y logic) */
  dy: number
  /** Font size in document pixels, sampled once per (respondent, field_type) pair */
  fontSize: number
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

function makePreview(provider: string, jitter_x: number, jitter_y: number, fontSize: number): ZonePreviewData {
  return {
    text: generateFakerValue(provider),
    // Python: jitter_x=0 → x1 + 0.05*w; jitter_x>0 → Gaussian(mean=0.12, σ=jitter_x)
    dx: sampleFraction(jitter_x, 0.12, 0.05),
    // Python: jitter_y=0 → y1 + 0.10*h; jitter_y>0 → Gaussian(mean=0.50, σ=jitter_y)
    dy: sampleFraction(jitter_y, 0.50, 0.10),
    fontSize,
  }
}

export function useZonePreview() {
  const [previews, setPreviews] = useState<Record<string, ZonePreviewData>>({})
  // Cache one font size per (respondent_id, field_type_id) so all zones sharing a
  // writing style render at the same size, while still being random within the range.
  const fontSizeCache = useRef<Record<string, number>>({})

  const getOrSampleFontSize = (respondentId: string, fieldTypeId: string, range: [number, number]): number => {
    const key = `${respondentId}:${fieldTypeId}`
    if (fontSizeCache.current[key] === undefined) {
      fontSizeCache.current[key] = Math.round(range[0] + Math.random() * (range[1] - range[0]))
    }
    return fontSizeCache.current[key]
  }

  const initZone = useCallback((zone: ZoneConfig, jitter_x = 0, jitter_y = 0, font_size_range: [number, number] = [12, 12]) => {
    const fontSize = getOrSampleFontSize(zone.respondent_id, zone.field_type_id ?? '', font_size_range)
    setPreviews(prev => ({ ...prev, [zone.zone_id]: makePreview(zone.faker_provider, jitter_x, jitter_y, fontSize) }))
  }, [])

  const rerollZone = useCallback((zone_id: string, provider: string, jitter_x = 0, jitter_y = 0) => {
    // Keep the existing cached font size — only text and position reroll
    setPreviews(prev => {
      const existing = prev[zone_id]
      return { ...prev, [zone_id]: makePreview(provider, jitter_x, jitter_y, existing?.fontSize ?? 12) }
    })
  }, [])

  const removeZone = useCallback((zone_id: string) => {
    setPreviews(prev => {
      const next = { ...prev }
      delete next[zone_id]
      return next
    })
  }, [])

  // Call when font_size_range changes so the next initZone/rerollZone resamples
  const clearFieldTypeFontSize = useCallback((respondentId: string, fieldTypeId: string) => {
    delete fontSizeCache.current[`${respondentId}:${fieldTypeId}`]
  }, [])

  // Immediately resample and apply a new font size for all zones of a given writing style.
  // Only fontSize changes — text and position are preserved.
  const resampleFontSize = useCallback((
    respondentId: string,
    fieldTypeId: string,
    range: [number, number],
    zoneIds: string[],
  ) => {
    const key = `${respondentId}:${fieldTypeId}`
    const newSize = Math.round(range[0] + Math.random() * (range[1] - range[0]))
    fontSizeCache.current[key] = newSize
    setPreviews(prev => {
      const next = { ...prev }
      for (const id of zoneIds) {
        if (next[id]) next[id] = { ...next[id], fontSize: newSize }
      }
      return next
    })
  }, [])

  return { previews, initZone, rerollZone, removeZone, clearFieldTypeFontSize, resampleFontSize }
}
