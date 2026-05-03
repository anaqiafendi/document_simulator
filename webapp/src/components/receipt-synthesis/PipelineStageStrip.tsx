import { Fragment, type CSSProperties } from 'react'
import type { ReceiptRenderResponse, StageOutput } from '../../types'
import PipelineStageCard from './PipelineStageCard'

interface StageDef {
  id: string             // matches StageOutput.stage; or 'final' for synthetic Final card
  label: string
  emoji: string
  /** Hard-disabled — card is unclickable. Used for Camera FX (v1.0). */
  disabled?: boolean
  disabledReason?: string
}

// Six visible cards in fixed order. The Final card mirrors the response's
// final_image_b64 and is purely a UI affordance (not a real backend stage).
//
// v0.3d: 3D Scene is no longer hard-disabled — it always activates so the user
// can click it. The strip computes a soft "Enable 3D" hint at render time when
// the response doesn't contain a `3d_render` stage. Camera FX stays disabled
// until v1.0.
const STAGES: StageDef[] = [
  { id: 'content',   label: 'Content',   emoji: '📋' },
  { id: 'raster',    label: 'Raster',    emoji: '📃' },
  { id: 'augraphy',  label: 'Augraphy',  emoji: '🎨' },
  { id: '3d_render', label: '3D Scene',  emoji: '🪑' },
  { id: 'camera_fx', label: 'Camera FX', emoji: '📷', disabled: true, disabledReason: 'Coming in v1.0' },
  { id: 'final',     label: 'Final',     emoji: '✅' },
]

interface PipelineStageStripProps {
  response: ReceiptRenderResponse | null
  selectedStage: string
  onSelectStage: (stage: string) => void
  dim?: boolean
}

const stripStyle: CSSProperties = {
  display: 'flex',
  gap: 10,
  alignItems: 'stretch',
  overflowX: 'auto',
  padding: '4px 2px 12px',
}

const arrow: CSSProperties = {
  alignSelf: 'center',
  color: '#bbb',
  fontSize: 18,
  flex: '0 0 auto',
  userSelect: 'none',
}

function stageBadge(stage: StageOutput | null, response: ReceiptRenderResponse | null, id: string): string | null {
  if (id === 'content') {
    return response ? `${response.ground_truth.tokens.length} tok` : null
  }
  if (stage) {
    return `${stage.elapsed_ms} ms`
  }
  return null
}

export default function PipelineStageStrip({
  response,
  selectedStage,
  onSelectStage,
  dim = false,
}: PipelineStageStripProps) {
  const stagesByName: Record<string, StageOutput> = {}
  if (response) {
    for (const s of response.stages) stagesByName[s.stage] = s
  }

  return (
    <div style={{ ...stripStyle, opacity: dim ? 0.55 : 1, transition: 'opacity 0.15s' }}>
      {STAGES.map((def, idx) => {
        const stage = stagesByName[def.id] ?? null
        // Final card uses final_image_b64; other cards use their stage's image_b64.
        const thumb =
          def.id === 'final'
            ? response?.final_image_b64 ?? null
            : stage?.image_b64 ?? null
        const badge = stageBadge(stage, response, def.id)
        const selected = selectedStage === def.id

        // For the 3D card: if the response exists but has no 3d_render stage,
        // the user opted out of render_3d — surface a hint but still allow
        // clicking so the card can show a "no image yet" placeholder.
        let hint: string | null = null
        if (def.id === '3d_render' && response && !stage) {
          hint = 'Enable 3D'
        }

        return (
          <Fragment key={def.id}>
            <PipelineStageCard
              stageId={def.id}
              label={def.label}
              emoji={def.emoji}
              thumbnailB64={thumb}
              badge={badge}
              selected={selected}
              disabled={def.disabled}
              disabledReason={def.disabledReason}
              hint={hint}
              onClick={() => onSelectStage(def.id)}
            />
            {idx < STAGES.length - 1 && <span style={arrow} aria-hidden="true">→</span>}
          </Fragment>
        )
      })}
    </div>
  )
}
