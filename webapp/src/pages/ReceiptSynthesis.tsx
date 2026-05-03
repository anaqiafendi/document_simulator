import { useEffect, useState, type CSSProperties } from 'react'
import { useReceiptSynthesis } from '../hooks/useReceiptSynthesis'
import { listTemplates, listAugraphyPresets, listHdriThumbnails } from '../api/client'
import type { TemplateInfoReceipt, HDRIInfo } from '../types'
import PipelineStageStrip from '../components/receipt-synthesis/PipelineStageStrip'
import StageInspector from '../components/receipt-synthesis/StageInspector'
import HDRIPicker from '../components/receipt-synthesis/HDRIPicker'

const NONE_PRESET = 'none'

const pageWrap: CSSProperties = {
  maxWidth: 1400,
  margin: '0 auto',
  padding: '24px 24px',
  boxSizing: 'border-box',
}

const card: CSSProperties = {
  background: '#fff',
  borderRadius: 8,
  border: '1px solid #e0e0e0',
  padding: '14px 18px',
}

const label: CSSProperties = {
  fontSize: 12,
  fontWeight: 600,
  color: '#555',
  display: 'block',
  marginBottom: 4,
}

const select: CSSProperties = {
  fontSize: 13,
  padding: '6px 10px',
  borderRadius: 5,
  border: '1px solid #ccc',
  background: '#fff',
  minWidth: 180,
}

const numberInput: CSSProperties = {
  fontSize: 13,
  padding: '6px 8px',
  borderRadius: 5,
  border: '1px solid #ccc',
  width: 110,
}

const btnPrimary: CSSProperties = {
  padding: '8px 18px',
  borderRadius: 6,
  border: 'none',
  cursor: 'pointer',
  fontSize: 14,
  fontWeight: 600,
  background: '#4f6ef7',
  color: '#fff',
  display: 'inline-flex',
  alignItems: 'center',
  gap: 8,
}

const btnDisabled: CSSProperties = {
  ...btnPrimary,
  background: '#aab',
  cursor: 'not-allowed',
}

const btnSecondary: CSSProperties = {
  padding: '6px 12px',
  borderRadius: 5,
  border: '1px solid #ccc',
  background: '#fafafa',
  cursor: 'pointer',
  fontSize: 13,
  color: '#333',
}

const errorBanner: CSSProperties = {
  background: '#fdecea',
  color: '#c0392b',
  border: '1px solid #f5c6c0',
  padding: '10px 14px',
  borderRadius: 6,
  fontSize: 13,
  margin: '12px 0',
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  gap: 12,
}

const renderHint: CSSProperties = {
  fontSize: 12,
  color: '#4f6ef7',
  fontStyle: 'italic',
  marginTop: 6,
  textAlign: 'right',
}

const toggleRow: CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: 6,
  fontSize: 13,
  color: '#333',
  cursor: 'pointer',
  userSelect: 'none',
}

const sliderInput: CSSProperties = {
  width: 140,
  verticalAlign: 'middle',
}

function Spinner() {
  return (
    <span
      aria-label="Loading"
      style={{
        display: 'inline-block',
        width: 14,
        height: 14,
        border: '2px solid rgba(255,255,255,0.4)',
        borderTopColor: '#fff',
        borderRadius: '50%',
        animation: 'rs-spin 0.8s linear infinite',
      }}
    />
  )
}

// One-time keyframe injection (no CSS modules in this codebase)
function useSpinnerStyles() {
  useEffect(() => {
    const id = 'rs-spin-style'
    if (document.getElementById(id)) return
    const s = document.createElement('style')
    s.id = id
    s.textContent = '@keyframes rs-spin { to { transform: rotate(360deg); } }'
    document.head.appendChild(s)
  }, [])
}

export default function ReceiptSynthesis() {
  useSpinnerStyles()
  const synth = useReceiptSynthesis()

  const [templates, setTemplates] = useState<TemplateInfoReceipt[]>([])
  const [presets, setPresets] = useState<string[]>([])
  const [loadingMeta, setLoadingMeta] = useState<boolean>(true)
  const [metaError, setMetaError] = useState<string | null>(null)
  const [bannerDismissed, setBannerDismissed] = useState<boolean>(false)

  // ── HDRI list state ──
  const [hdris, setHdris] = useState<HDRIInfo[]>([])
  const [hdriLoading, setHdriLoading] = useState<boolean>(true)
  const [hdriError, setHdriError] = useState<string | null>(null)
  const [hdriRetryNonce, setHdriRetryNonce] = useState<number>(0)

  // Load templates + augraphy presets on mount
  useEffect(() => {
    let cancelled = false
    setLoadingMeta(true)
    Promise.all([listTemplates(), listAugraphyPresets()])
      .then(([t, p]) => {
        if (cancelled) return
        setTemplates(t.templates)
        setPresets(p.presets)
        // If the current request.template isn't in the returned list, default
        // to the first one so the dropdown stays in sync with the backend.
        if (t.templates.length > 0 && !t.templates.find(tt => tt.id === synth.request.template)) {
          synth.setRequest({ template: t.templates[0].id })
        }
      })
      .catch(e => {
        if (cancelled) return
        setMetaError(e instanceof Error ? e.message : 'Failed to load metadata')
      })
      .finally(() => {
        if (cancelled) return
        setLoadingMeta(false)
      })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Load HDRI thumbnails on mount (and on retry). Failures degrade gracefully
  // — the picker shows an empty state with a retry button.
  useEffect(() => {
    let cancelled = false
    setHdriLoading(true)
    setHdriError(null)
    listHdriThumbnails()
      .then(res => {
        if (cancelled) return
        setHdris(res.hdris)
        // If the current selection isn't in the returned list, pick the first
        // one so the picker has a valid default once 3D is enabled.
        if (res.hdris.length > 0 && !res.hdris.find(h => h.id === synth.request.hdri_id)) {
          synth.setRequest({ hdri_id: res.hdris[0].id })
        }
      })
      .catch(e => {
        if (cancelled) return
        setHdriError(e instanceof Error ? e.message : 'Failed to load HDRIs')
      })
      .finally(() => {
        if (cancelled) return
        setHdriLoading(false)
      })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hdriRetryNonce])

  // Reset the dismissed flag whenever a fresh error comes in
  useEffect(() => {
    if (synth.error) setBannerDismissed(false)
  }, [synth.error])

  const handlePresetChange = (v: string) => {
    synth.setRequest({ augraphy_preset: v === NONE_PRESET ? null : v })
  }

  const presetValue = synth.request.augraphy_preset ?? NONE_PRESET
  const canRender = !synth.isRendering && !!synth.request.template
  const render3D = synth.request.render_3d ?? false
  const curlStrength = synth.request.curl_strength ?? 0.1

  return (
    <div style={pageWrap}>
      <h2 style={{ margin: '0 0 4px', fontSize: 22 }}>Receipt Synthesis</h2>
      <p style={{ color: '#666', margin: '0 0 20px', fontSize: 14 }}>
        Generate photoreal receipts and inspect every pipeline stage. Pick a template, set a seed,
        choose an Augraphy preset, optionally enable 3D, then click <strong>Render Preview</strong>.
      </p>

      {/* ── Top controls ─────────────────────────────────────────────── */}
      <div style={{ ...card, marginBottom: 12 }}>
        <div style={{ display: 'flex', gap: 18, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div>
            <label style={label} htmlFor="rs-template">Template</label>
            <select
              id="rs-template"
              value={synth.request.template}
              onChange={e => synth.setRequest({ template: e.target.value })}
              disabled={loadingMeta || templates.length === 0}
              style={select}
            >
              {loadingMeta && <option value={synth.request.template}>Loading…</option>}
              {!loadingMeta && templates.length === 0 && (
                <option value={synth.request.template}>{synth.request.template}</option>
              )}
              {templates.map(t => (
                <option key={t.id} value={t.id}>
                  {t.name} ({t.sample_token_count} tok)
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={label} htmlFor="rs-seed">Seed</label>
            <div style={{ display: 'flex', gap: 6 }}>
              <input
                id="rs-seed"
                type="number"
                min={0}
                value={synth.request.seed}
                onChange={e => synth.setRequest({ seed: Math.max(0, parseInt(e.target.value) || 0) })}
                style={numberInput}
              />
              <button
                type="button"
                onClick={synth.rerollSeed}
                style={btnSecondary}
                title="Roll a new random seed"
                aria-label="Reroll seed"
              >
                ⟳
              </button>
            </div>
          </div>

          <div>
            <label style={label} htmlFor="rs-aug">Augraphy preset</label>
            <select
              id="rs-aug"
              value={presetValue}
              onChange={e => handlePresetChange(e.target.value)}
              disabled={loadingMeta}
              style={select}
            >
              <option value={NONE_PRESET}>none (skip Augraphy)</option>
              {presets.map(p => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>

          <div>
            <span style={label}>3D Scene</span>
            <label style={toggleRow} title="Render the receipt into a programmatic 3D scene with HDRI lighting.">
              <input
                type="checkbox"
                checked={render3D}
                onChange={() => synth.enable3DToggle()}
              />
              Enable 3D
            </label>
          </div>

          <div style={{ marginLeft: 'auto' }}>
            <button
              type="button"
              onClick={synth.render}
              disabled={!canRender}
              style={canRender ? btnPrimary : btnDisabled}
            >
              {synth.isRendering ? <><Spinner /> Rendering…</> : 'Render Preview'}
            </button>
            {synth.isRendering && synth.showLongRenderHint && (
              <div style={renderHint} role="status" aria-live="polite">
                {render3D
                  ? 'Rendering 3D scene… (this can take 5-15s)'
                  : 'Still rendering…'}
              </div>
            )}
          </div>
        </div>

        {/* ── 3D-only secondary controls (revealed only when 3D is on) ── */}
        {render3D && (
          <div style={{
            marginTop: 14,
            paddingTop: 12,
            borderTop: '1px dashed #e0e0e0',
            display: 'flex',
            gap: 24,
            alignItems: 'flex-start',
            flexWrap: 'wrap',
          }}>
            <div style={{ flex: '0 0 auto' }}>
              <span style={label}>HDRI lighting</span>
              <HDRIPicker
                hdris={hdris}
                selectedId={synth.request.hdri_id ?? null}
                onSelect={id => synth.setRequest({ hdri_id: id })}
                loading={hdriLoading}
                error={hdriError}
                onRetry={() => setHdriRetryNonce(n => n + 1)}
                enabled={render3D}
              />
            </div>

            <div style={{ flex: '0 0 auto', minWidth: 180 }}>
              <label style={label} htmlFor="rs-curl">
                Paper curl: <strong>{curlStrength.toFixed(2)}</strong>
              </label>
              <input
                id="rs-curl"
                type="range"
                min={0}
                max={0.5}
                step={0.01}
                value={curlStrength}
                onChange={e => synth.setRequest({ curl_strength: parseFloat(e.target.value) })}
                style={sliderInput}
                aria-label="Paper curl strength"
              />
              <div style={{ fontSize: 11, color: '#888', marginTop: 2 }}>
                0.0 = flat, 0.5 = strongly curled.
              </div>
            </div>
          </div>
        )}

        {/* Selected template description */}
        {(() => {
          const t = templates.find(tt => tt.id === synth.request.template)
          return t ? (
            <div style={{ marginTop: 10, fontSize: 12, color: '#666' }}>
              <strong>{t.name}</strong>: {t.description}
            </div>
          ) : null
        })()}

        {metaError && (
          <div style={{ ...errorBanner, marginTop: 12, marginBottom: 0 }}>
            <span>Couldn't load template / preset list: {metaError}</span>
          </div>
        )}
      </div>

      {/* ── Render error banner (non-modal) ──────────────────────────── */}
      {synth.error && !bannerDismissed && (
        <div style={errorBanner} role="alert">
          <span><strong>Render failed.</strong> {synth.error}</span>
          <button
            type="button"
            onClick={() => setBannerDismissed(true)}
            style={{ ...btnSecondary, padding: '4px 10px', fontSize: 12 }}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* ── Stage strip ──────────────────────────────────────────────── */}
      <div style={{ ...card, padding: '10px 14px', marginTop: 4 }}>
        <PipelineStageStrip
          response={synth.response}
          selectedStage={synth.selectedStage}
          onSelectStage={synth.setSelectedStage}
          dim={synth.isRendering}
        />
        {!synth.response && !synth.isRendering && (
          <div style={{ textAlign: 'center', color: '#aaa', fontSize: 13, padding: '20px 0 8px' }}>
            Click <strong>Render Preview</strong> to populate the pipeline.
          </div>
        )}
      </div>

      {/* ── Inspector ────────────────────────────────────────────────── */}
      {synth.response && (
        <StageInspector
          response={synth.response}
          selectedStage={synth.selectedStage}
          showBboxes={synth.showBboxes}
          setShowBboxes={synth.setShowBboxes}
          showLabels={synth.showLabels}
          setShowLabels={synth.setShowLabels}
        />
      )}
    </div>
  )
}
