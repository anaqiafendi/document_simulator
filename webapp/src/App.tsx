import { useEffect, useState } from 'react'
import { useTemplate } from './hooks/useTemplate'
import { useZones } from './hooks/useZones'
import { useRespondents } from './hooks/useRespondents'
import { usePreviews } from './hooks/usePreviews'
import { useGenerate } from './hooks/useGenerate'
import { useZonePreview } from './hooks/useZonePreview'
import StatusBar from './components/StatusBar'
import ZoneCanvas from './components/ZoneCanvas'
import RespondentPanel from './components/RespondentPanel'
import PreviewGallery from './components/PreviewGallery'
import BatchGeneratePanel from './components/BatchGeneratePanel'
import ConfigPanel from './components/ConfigPanel'
import type { SynthesisConfig, ZoneConfig } from './types'

const sectionHead: React.CSSProperties = {
  fontSize: 11, fontWeight: 700, letterSpacing: '0.06em',
  textTransform: 'uppercase', color: '#888',
  margin: '0 0 8px 0', paddingBottom: 4, borderBottom: '1px solid #eee',
}

export default function App() {
  const template = useTemplate()
  const zones = useZones()
  const respondents = useRespondents()
  const previews = usePreviews()
  const gen = useGenerate()
  const zonePreview = useZonePreview()

  // Enhancement 7: lift activeRespondentId so RespondentPanel can show the "Active" badge
  const [activeRespondentId, setActiveRespondentId] = useState<string | undefined>(undefined)

  // Enhancement 5: Cmd+Z / Ctrl+Z undo
  useEffect(() => {
    const handle = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'z') {
        const tag = (document.activeElement as HTMLElement)?.tagName
        if (tag === 'INPUT' || tag === 'TEXTAREA') return
        e.preventDefault()
        zones.undo()
      }
    }
    window.addEventListener('keydown', handle)
    return () => window.removeEventListener('keydown', handle)
  }, [zones.undo])

  const buildConfig = (outputDir = '/tmp/synthetic_output', n = 10): SynthesisConfig => ({
    respondents: respondents.respondents,
    zones: zones.zones,
    generator: {
      image_width: template.templateInfo?.width_px ?? 800,
      image_height: template.templateInfo?.height_px ?? 1000,
      output_dir: outputDir,
      seed: 42,
      n,
    },
  })

  // Look up jitter values for a zone from the respondent config
  const getJitter = (zone: ZoneConfig) => {
    const r = respondents.respondents.find(r => r.respondent_id === zone.respondent_id)
    const ft = r?.field_types.find(ft => ft.field_type_id === zone.field_type_id) ?? r?.field_types[0]
    return { jitter_x: ft?.jitter_x ?? 0, jitter_y: ft?.jitter_y ?? 0 }
  }

  // Wrap addZone to also initialise faker preview text with jitter offsets and font size
  const handleZoneDrawn = (partial: Omit<ZoneConfig, 'zone_id'>) => {
    const newZone = zones.addZone(partial)
    const r = respondents.respondents.find(r => r.respondent_id === partial.respondent_id)
    const ft = r?.field_types.find(ft => ft.field_type_id === partial.field_type_id) ?? r?.field_types[0]
    zonePreview.initZone(newZone, ft?.jitter_x ?? 0, ft?.jitter_y ?? 0, ft?.font_size_range ?? [12, 12])
  }

  // Wrap removeZone to also remove preview text
  const handleZoneRemove = (zone_id: string) => {
    zones.removeZone(zone_id)
    zonePreview.removeZone(zone_id)
  }

  // Wrap updateZone: if faker_provider changed, auto-reroll preview
  const handleZoneUpdate = (zone_id: string, patch: Partial<ZoneConfig>) => {
    zones.updateZone(zone_id, patch)
    if (patch.faker_provider || patch.field_type_id) {
      const updatedZone = { ...zones.zones.find(z => z.zone_id === zone_id)!, ...patch }
      const { jitter_x, jitter_y } = getJitter(updatedZone)
      zonePreview.rerollZone(zone_id, updatedZone.faker_provider, jitter_x, jitter_y)
    }
  }

  // When field type properties change, reroll affected zones
  const handleUpdateFieldType = (respondentId: string, ftId: string, patch: Partial<import('./types').FieldTypeConfig>) => {
    respondents.updateFieldType(respondentId, ftId, patch)
    const r = respondents.respondents.find(r => r.respondent_id === respondentId)
    const ft = r?.field_types.find(ft => ft.field_type_id === ftId)
    if (!ft) return
    // When font_size_range changes, clear the cached size so next reroll resamples
    if (patch.font_size_range) {
      zonePreview.clearFieldTypeFontSize(respondentId, ftId)
    }
    if (patch.jitter_x !== undefined || patch.jitter_y !== undefined) {
      const jx = patch.jitter_x ?? ft.jitter_x
      const jy = patch.jitter_y ?? ft.jitter_y
      zones.zones
        .filter(z => z.respondent_id === respondentId && z.field_type_id === ftId)
        .forEach(z => zonePreview.rerollZone(z.zone_id, z.faker_provider, jx, jy))
    }
  }

  const anyError = template.error ?? previews.error ?? gen.error

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', maxWidth: 1400, margin: '0 auto', padding: '16px 24px' }}>
      {/* Top bar */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 16, marginBottom: 4 }}>
        <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Synthetic Document Generator</h1>
        <StatusBar />
      </div>

      {anyError && (
        <div style={{ color: '#c0392b', background: '#fdecea', padding: '7px 12px', borderRadius: 4, marginBottom: 12, fontSize: 13 }}>
          {anyError}
        </div>
      )}

      {/* Template upload row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
        <label style={{ fontSize: 13, fontWeight: 600, color: '#555' }}>Template</label>

        <input
          type="file"
          accept=".pdf,.png,.jpg,.jpeg"
          disabled={template.loading}
          onChange={e => { const f = e.target.files?.[0]; if (f) template.upload(f) }}
        />

        {template.samples.length > 0 && (
          <select
            defaultValue=""
            onChange={e => { if (e.target.value) template.loadFromSample(e.target.value) }}
            style={{ fontSize: 12 }}
          >
            <option value="" disabled>or load sample…</option>
            {template.samples.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        )}

        {template.loading && <span style={{ fontSize: 12, color: '#999' }}>Loading…</span>}
        {template.templateInfo && (
          <span style={{ fontSize: 12, color: '#777' }}>
            {template.templateInfo.width_px}&times;{template.templateInfo.height_px}px
            {template.templateInfo.is_pdf ? ' · PDF' : ' · Image'}
          </span>
        )}

        <span style={{ marginLeft: 'auto' }}>
          <ConfigPanel config={buildConfig()} onLoad={() => {}} />
        </span>
      </div>

      {/* Main 2-column layout */}
      <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>

        {/* ── Left: canvas ── */}
        <div style={{ flex: '1 1 0', minWidth: 0 }}>
          {template.templateInfo ? (
            <ZoneCanvas
              templateInfo={template.templateInfo}
              zones={zones.zones}
              selectedId={zones.selectedId}
              respondents={respondents.respondents}
              zonePreviews={zonePreview.previews}
              activeRespondentId={activeRespondentId}
              onZoneDrawn={handleZoneDrawn}
              onZoneSelect={zones.selectZone}
              onZoneUpdate={handleZoneUpdate}
              onZoneRemove={handleZoneRemove}
              onActiveRespondentChange={setActiveRespondentId}
            />
          ) : (
            <div style={{
              border: '2px dashed #ddd', borderRadius: 6, height: 420,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#bbb', fontSize: 14,
            }}>
              Upload a PDF / image or pick a sample above to begin
            </div>
          )}
        </div>

        {/* ── Right: sidebar ── */}
        <div style={{
          flex: '0 0 380px', width: 380,
          position: 'sticky', top: 16,
          maxHeight: 'calc(100vh - 80px)',
          overflowY: 'auto',
        }}>
          <h3 style={sectionHead}>Respondents &amp; Zones</h3>
          <RespondentPanel
            respondents={respondents.respondents}
            zones={zones.zones}
            selectedZoneId={zones.selectedId}
            zonePreviews={zonePreview.previews}
            activeRespondentId={activeRespondentId}
            onAdd={respondents.addRespondent}
            onRemove={respondents.removeRespondent}
            onUpdate={respondents.updateRespondent}
            onAddFieldType={respondents.addFieldType}
            onRemoveFieldType={respondents.removeFieldType}
            onUpdateFieldType={handleUpdateFieldType}
            onActivate={setActiveRespondentId}
            onSelectZone={zones.selectZone}
            onUpdateZone={handleZoneUpdate}
            onRemoveZone={handleZoneRemove}
            onRerollZone={(zone_id, provider) => {
              const zone = zones.zones.find(z => z.zone_id === zone_id)
              if (!zone) return
              const { jitter_x, jitter_y } = getJitter(zone)
              zonePreview.rerollZone(zone_id, provider, jitter_x, jitter_y)
            }}
          />
        </div>
      </div>

      {/* ── Bottom: preview + generate ── */}
      <div style={{ marginTop: 28, display: 'flex', gap: 32, flexWrap: 'wrap' }}>
        <section style={{ flex: '1 1 500px' }}>
          <h3 style={sectionHead}>Preview</h3>
          <PreviewGallery
            previews={previews.previews}
            loading={previews.loading}
            config={buildConfig()}
            onPreview={() => previews.loadPreviews(buildConfig())}
            onReroll={idx => previews.reroll(idx, buildConfig())}
          />
        </section>

        <section style={{ flex: '0 0 340px' }}>
          <h3 style={sectionHead}>Generate Batch</h3>
          <BatchGeneratePanel
            loading={gen.loading}
            jobStatus={gen.jobStatus}
            downloadJobId={gen.downloadJobId}
            onGenerate={(n, dir) => gen.generate(buildConfig(dir, n), n)}
            downloadUrl={gen.downloadUrl}
          />
        </section>
      </div>
    </div>
  )
}


