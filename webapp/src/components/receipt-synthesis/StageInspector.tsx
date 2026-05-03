import { useState, type CSSProperties } from 'react'
import type {
  CoordSnapshotStage,
  ReceiptRenderResponse,
  StageOutput,
} from '../../types'
import BboxOverlay from './BboxOverlay'
import TokenList from './TokenList'

interface StageInspectorProps {
  response: ReceiptRenderResponse
  selectedStage: string  // stage card id (could be 'final')
  showBboxes: boolean
  setShowBboxes: (v: boolean) => void
  showLabels: boolean
  setShowLabels: (v: boolean) => void
}

// Map a pipeline-stage id (from PipelineStageCard) → which CoordSnapshot.stage
// to draw on top of that image. v0.2 only emits `html` and `raster` snapshots
// (the post-Augraphy image is geometrically identical to raster, so we re-use
// the raster polygons there). The 3D / camera_fx / final_crop snapshots are
// reserved for v0.3 / v1.0.
function snapshotStageFor(stageId: string): CoordSnapshotStage {
  switch (stageId) {
    case 'content':
      return 'html'
    case 'raster':
    case 'augraphy':
      return 'raster'
    case '3d_render':
      return 'camera_2d'
    case 'camera_fx':
      return 'camera_fx'
    case 'final':
      return 'final_crop'
    default:
      return 'raster'
  }
}

// Find the StageOutput for a card id, respecting the synthetic 'final' card.
function findStageOutput(
  response: ReceiptRenderResponse,
  stageId: string,
): { image: string | null; output: StageOutput | null } {
  if (stageId === 'final') {
    // The 'final' card mirrors the last executed stage's image_b64 (which the
    // backend also exposes as response.final_image_b64). Use the last executed
    // stage's parameters for the inspector's parameter dump.
    const last = response.stages[response.stages.length - 1] ?? null
    return { image: response.final_image_b64, output: last }
  }
  const out = response.stages.find(s => s.stage === stageId) ?? null
  return { image: out?.image_b64 ?? null, output: out }
}

const panelCard: CSSProperties = {
  background: '#fff',
  border: '1px solid #e8e8e8',
  borderRadius: 8,
  padding: 14,
}

const sectionTitle: CSSProperties = {
  fontSize: 11,
  fontWeight: 700,
  letterSpacing: '0.06em',
  textTransform: 'uppercase',
  color: '#888',
  margin: '0 0 8px',
}

const checkboxLabel: CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: 5,
  fontSize: 13,
  color: '#333',
  cursor: 'pointer',
}

export default function StageInspector({
  response,
  selectedStage,
  showBboxes,
  setShowBboxes,
  showLabels,
  setShowLabels,
}: StageInspectorProps) {
  const [highlight, setHighlight] = useState<string | null>(null)
  const { image, output } = findStageOutput(response, selectedStage)
  const snapshotStage = snapshotStageFor(selectedStage)
  const hasImage = !!image

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 2fr) minmax(280px, 1fr)', gap: 16, marginTop: 16 }}>
      {/* Left: image + overlay controls */}
      <div style={panelCard}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, gap: 12, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 14, fontWeight: 700, color: '#333', textTransform: 'capitalize' }}>
              {selectedStage.replace('_', ' ')} stage
            </span>
            {output && (
              <span style={{ fontSize: 11, color: '#888' }}>
                {output.elapsed_ms} ms
              </span>
            )}
          </div>
          <div style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
            <label style={checkboxLabel}>
              <input type="checkbox" checked={showBboxes} onChange={e => setShowBboxes(e.target.checked)} />
              Show bboxes
            </label>
            <label style={{ ...checkboxLabel, opacity: showBboxes ? 1 : 0.5 }}>
              <input
                type="checkbox"
                checked={showLabels}
                onChange={e => setShowLabels(e.target.checked)}
                disabled={!showBboxes}
              />
              Show labels
            </label>
          </div>
        </div>

        {hasImage ? (
          <BboxOverlay
            imageB64={image!}
            tokens={response.ground_truth.tokens}
            stage={snapshotStage}
            showBboxes={showBboxes}
            showLabels={showLabels}
            highlightTokenId={highlight}
            onSelectToken={tid => setHighlight(prev => (prev === tid ? null : tid))}
          />
        ) : (
          <div style={{
            padding: '40px 20px', textAlign: 'center', color: '#999',
            fontSize: 13, background: '#fafafa', borderRadius: 4, border: '1px dashed #ddd',
          }}>
            This stage emits no image (token-only output).
          </div>
        )}
      </div>

      {/* Right: parameters + token list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, minWidth: 0 }}>
        <div style={panelCard}>
          <h3 style={sectionTitle}>Parameters</h3>
          {output && Object.keys(output.parameters).length > 0 ? (
            <pre style={{
              margin: 0, fontSize: 11, lineHeight: 1.45, color: '#333',
              background: '#fafafa', padding: 8, borderRadius: 4, maxHeight: 180,
              overflowY: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
            }}>
              {JSON.stringify(output.parameters, null, 2)}
            </pre>
          ) : (
            <div style={{ fontSize: 12, color: '#aaa', fontStyle: 'italic' }}>No parameters.</div>
          )}
        </div>

        <div style={panelCard}>
          <h3 style={sectionTitle}>
            Tokens ({response.ground_truth.tokens.length})
          </h3>
          <TokenList
            tokens={response.ground_truth.tokens}
            highlightTokenId={highlight}
            onSelectToken={tid => setHighlight(prev => (prev === tid ? null : tid))}
          />
        </div>
      </div>
    </div>
  )
}
