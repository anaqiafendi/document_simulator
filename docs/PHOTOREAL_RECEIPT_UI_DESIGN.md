# Photorealistic Receipt Synthesis — UI Exposure Design

**Goal**: every pipeline stage (content → raster → Augraphy → 3D scene → camera FX → final photo) is **previewable + interactable** in the React webapp. Users see what the pipeline did at every step and can tweak parameters that drive each stage.

**Stack decision (callout from user, 2026-05-03)**: React webapp at `webapp/` (not Streamlit). The Streamlit pages are sunsetted per FDD #25. All UI work for receipt synthesis goes through the React + FastAPI stack.

This document is the source of truth for UI-related decisions across phases v0.2 → v1.0. Each phase's FDD references this doc and implements its slice.

---

## 1. Mental model — the stage strip

Receipt photo synthesis is fundamentally a **chain of transformations**. The most honest UI surfaces that chain directly: one card per stage, arranged left-to-right, each showing what came out of that stage and what knobs control it.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  Receipt Synthesis                                            [Render Preview] │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   Top controls: Template ▾ | Seed [42] ⟳ | Augraphy preset ▾ | Save preset… │
│                                                                                │
├──── Stage strip ───────────────────────────────────────────────────────────────┤
│                                                                                │
│   ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐    │
│   │Content │→ │ Raster │→ │Augraphy│→ │  3D   │→ │ Camera │→ │ Final  │    │
│   │  📋    │  │  📃    │  │  🎨    │  │  🪑    │  │  📷    │  │  ✅    │    │
│   │ ◯◯◯◯◯ │  │ [img]  │  │ [img]  │  │ [img]  │  │ [img]  │  │ [img]  │    │
│   │ 8 toks │  │ 12 box │  │ scuffd │  │ tilted │  │ blur   │  │ +GT    │    │
│   └────────┘  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘    │
│       ▲           ▲                                                            │
│   click to inspect — opens inspector panel below                              │
│                                                                                │
├──── Stage inspector (when a card is clicked) ─────────────────────────────────┤
│                                                                                │
│  ┌──────────────────────────────────┐  ┌──────────────────────────────────┐  │
│  │   Stage image with bbox overlay  │  │  Parameters for this stage       │  │
│  │                                  │  │                                  │  │
│  │  [○] Show bboxes                 │  │  Template: thermal_minimal ▾     │  │
│  │  [○] Show token labels           │  │  Seed: [42]  ⟳ regenerate       │  │
│  │  Stage selector: raster ▾        │  │  Tax rate: [0.0825]              │  │
│  │                                  │  │                                  │  │
│  │  ┌──────────────────────────┐    │  │  [Apply & re-render from here]   │  │
│  │  │                          │    │  └──────────────────────────────────┘  │
│  │  │   [rendered receipt      │    │                                        │
│  │  │    + colored polygons]   │    │  ┌──────────────────────────────────┐  │
│  │  │                          │    │  │  Tokens (8)                      │  │
│  │  └──────────────────────────┘    │  │                                  │  │
│  │                                  │  │  merchant     "Acme Diner"       │  │
│  └──────────────────────────────────┘  │  address      "123 Main St…"     │  │
│                                        │  item_0_sku   "BURGER COMBO"     │  │
│                                        │  item_0_qty   "2"                │  │
│                                        │  …                               │  │
│                                        └──────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────┘
```

Three things make this work:

1. **All stages render in one backend call**. The `POST /api/receipt-synthesis/render` endpoint runs the full pipeline once and returns a base64 image *per stage* plus the consolidated `ImageGroundTruth`. The UI never round-trips per stage to inspect — it has the data already.
2. **Bbox overlays are client-side SVG over `<img>`**. Toggling `Show bboxes` is instant, no backend call. The polygons come from the appropriate `CoordSnapshot` in the GT.
3. **"Apply & re-render from here" propagates downstream**. Tweaking a stage 3 param re-runs stages 3-N (not 1-2). The backend supports a `start_stage` parameter to skip already-computed early stages and reuse their cached output.

---

## 2. Per-stage UI specification

| Stage | UI element | Image shown | Parameters exposed | Interactivity |
|---|---|---|---|---|
| **Content** | Card + JSON-tree popout | None (icon + token-count badge) | template, seed, locale, tax_rate (later: line-item count, payment method) | "Edit Receipt fields directly" modal for ad-hoc tweaks; "Save as preset" |
| **Raster** | Card + image | WeasyPrint output PNG | (none — driven entirely by Content + template) | Bbox overlay toggle; per-token label toggle; click polygon → highlight in token list |
| **Augraphy** *(v0.2+)* | Card + image | Post-degradation PNG | preset selector (light / medium / heavy); "regenerate seed for Augraphy"; per-effect toggles (ink-bleed, shadow, paper-texture) | Compare slider (Raster ↔ Augraphy) |
| **3D scene** *(v0.3+)* | Card + image | Camera-perspective render of receipt on mesh | HDRI selector (Poly Haven thumbnails); paper curl strength; camera angle (azimuth + elevation); hand visibility toggle; desk material | Stage selector dropdown shows any intermediate `CoordSnapshot` (uv / world / camera_2d / visibility) overlaid on this image — debug tool from plan §4 |
| **Camera FX** *(v1.0+)* | Card + image | Final photo with lens distortion + DoF + JPEG | DoF strength; lens distortion (barrel %); motion blur amount; auto-exposure offset; JPEG quality | "Re-roll just camera FX" — keeps 3D render, re-applies post FX with new seed |
| **Final + GT** | Card + image | Final photo with all GT polygons drawn | (read-only inspect) | Download PNG; download `gt.json`; download both as zip |

**Phase mapping**:
- **v0.2** ships the strip with Content + Raster + Augraphy + Final cards (the 3D + Camera cards render as "not yet available" placeholders so the UI surface is set early)
- **v0.3** activates the 3D card and the stage selector debug tool
- **v1.0** activates the Camera FX card

Reasoning: shipping the empty placeholders in v0.2 means later phases just *populate* existing UI surface — no nav restructure, no "where does this go" debates per phase.

---

## 3. Backend API surface

All endpoints under `/api/receipt-synthesis/`. Pydantic models live in `src/document_simulator/api/models.py` (the existing convention — no separate per-feature model file).

### v0.2 endpoints

```python
# Render the full pipeline once; return all stage intermediates + final GT
POST /api/receipt-synthesis/render
Request: ReceiptRenderRequest {
    template: str,                          # "thermal_minimal" | future templates
    seed: int,
    augraphy_preset: str | None = None,     # null = skip Augraphy stage
    start_stage: str | None = None,         # null = run from start; else "augraphy"|...
    cached_image_id: str | None = None,     # if start_stage given, cache key for upstream image
}
Response: ReceiptRenderResponse {
    image_id: str,                          # uuid for caching
    final_image_b64: str,
    ground_truth: ImageGroundTruth,         # the same Pydantic model from synthesis.receipts.schema
    stages: list[StageOutput],              # one per executed stage
    pipeline_version: str,
}
StageOutput {
    stage: Literal["content","raster","augraphy"],  # extended in v0.3+, v1.0
    image_b64: str | None,                  # null for "content" stage (no image yet)
    parameters: dict[str, Any],             # the parameters that drove this stage
    elapsed_ms: int,
}

# List available templates and Augraphy presets
GET /api/receipt-synthesis/templates       → { templates: list[TemplateInfo] }
GET /api/receipt-synthesis/augraphy-presets → { presets: list[str] }
```

### v0.3 additions

`StageOutput.stage` literal grows: `"3d_render" | "visibility"`. Response gains `scene_state: SceneState` for reproducibility. New `GET /api/receipt-synthesis/hdri-thumbnails` lists Poly Haven HDRIs as base64 thumbnails for the picker.

### v0.4 additions (batch)

```python
POST /api/receipt-synthesis/batch
Request: BatchRequest {
    template_distribution: dict[str, float],   # weighted template selection
    n_samples: int,
    augraphy_preset: str | None,
    sampler_config: ParameterSamplerConfig,    # Sobol / categorical / fixed per param
    output_dataset_name: str,
}
Response: { job_id: str }

GET /api/receipt-synthesis/batch/{job_id}      → JobStatusResponse (existing pattern)
GET /api/receipt-synthesis/batch/{job_id}/manifest.jsonl → JSONL stream
GET /api/receipt-synthesis/batch/{job_id}/download → FileResponse zip
```

### v1.0 additions

`StageOutput.stage` adds `"camera_fx"`. New `POST /api/receipt-synthesis/contact-sheet` returns a 4×8 grid of random samples for qualitative review.

### Caching strategy (back-end)

Already informed by plan doc §2: two layers — `@lru_cache` (per-process) for renderer/Jinja env singletons, `diskcache` keyed on `hash(json.dumps(stage_params, sort_keys=True))` for stage outputs. The `start_stage` + `cached_image_id` endpoint params let the UI skip re-rendering upstream stages when the user only changes a downstream parameter — directly hits the diskcache.

---

## 4. React component structure

Lives at `webapp/src/pages/ReceiptSynthesis.tsx`. Modeled after the existing `pages/AugmentationLab.tsx` pattern (state-heavy page with sub-components).

```
webapp/src/pages/ReceiptSynthesis.tsx                # page shell, top controls, stage state
webapp/src/components/receipt-synthesis/
  ├── PipelineStageStrip.tsx                         # horizontal strip of stage cards
  ├── PipelineStageCard.tsx                          # one card: thumbnail, label, badge, click-to-select
  ├── StageInspector.tsx                             # expanded inspector for selected stage
  ├── BboxOverlay.tsx                                # SVG polygons over an <img>; reusable across stages
  ├── ParameterForm.tsx                              # generic Pydantic-shaped form renderer
  ├── TokenList.tsx                                  # table of tokens with click → highlight on overlay
  ├── ReceiptContentEditor.tsx                       # JSON-tree editor for the Receipt model (v0.2 limited fields, full in v1.0)
  └── HDRIPicker.tsx                                 # v0.3+: thumbnail grid of Poly Haven HDRIs

webapp/src/api/client.ts                             # extend with: renderReceipt(), listTemplates(), listAugraphyPresets()
webapp/src/types/index.ts                            # extend with: ReceiptRenderRequest/Response, StageOutput, ImageGroundTruth, TokenGroundTruth
webapp/src/hooks/useReceiptSynthesis.ts              # state hook: current params, render, switch stage, toggle overlay
```

### NavBar registration

Add to `NAV_ITEMS` in `webapp/src/components/NavBar.tsx`:
```typescript
{ to: '/receipt-synthesis', label: 'Receipt Synthesis', emoji: '🧾' }
```

Add to `App.tsx`:
```tsx
<Route path="/receipt-synthesis" element={<ReceiptSynthesis />} />
```

### State shape (sketch)

```typescript
interface ReceiptSynthesisState {
  request: ReceiptRenderRequest;          // controlled by top controls + per-stage param forms
  response: ReceiptRenderResponse | null; // last successful render
  selectedStage: string;                  // which card is in the inspector
  showBboxes: boolean;
  showTokenLabels: boolean;
  overlayStage: string;                   // which CoordSnapshot stage to draw (defaults to current selectedStage)
  isRendering: boolean;
  error: string | null;
}
```

Top-level `useReceiptSynthesis()` hook owns this state, handles the API call, and exposes mutators. Each sub-component is dumb (props in, callbacks out).

### Bbox overlay implementation

```tsx
// BboxOverlay.tsx (sketch)
function BboxOverlay({ image, tokens, stage, showLabels }: Props) {
  const [imgW, imgH] = useImageDimensions(image);
  return (
    <div style={{ position: 'relative' }}>
      <img src={`data:image/png;base64,${image}`} alt="" />
      <svg viewBox={`0 0 ${imgW} ${imgH}`} style={{ position: 'absolute', inset: 0 }}>
        {tokens.map(t => {
          const snap = t.coords.find(c => c.stage === stage);
          if (!snap) return null;
          return (
            <g key={t.token_id}>
              <polygon
                points={snap.polygon.map(([x, y]) => `${x},${y}`).join(' ')}
                fill="none"
                stroke={colorForToken(t.token_id)}
                strokeWidth="1.5"
              />
              {showLabels && <text x={snap.polygon[0][0]} y={snap.polygon[0][1] - 2}>{t.token_id}</text>}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
```

Pure client-side — toggle is instantaneous. No special server round-trip for the overlay, just for the underlying image.

---

## 5. Parameter forms — strategy decision

**v0.2 — hand-write forms.** Only 4-5 parameters total (template, seed, augraphy preset, optional locale). Hand-written is faster than wiring up auto-generation.

**v0.3+ — evaluate auto-generation.** Once we have ~15 parameters across 3D scene + camera, hand-writing each form duplicates the Pydantic schema. Options:
- `pydantic-to-typescript` (codegen at build time) + a small `<ParameterForm schema={...} value={...} onChange={...}>` component that introspects the JSON schema
- Keep hand-writing — accept the duplication

Decision deferred to v0.3. Document the choice in the v0.3 FDD.

---

## 6. Batch tab (v0.4)

A separate page at `/receipt-synthesis/batch`, **not** another tab inside the main receipt synthesis page (different mental model: real-time tweak vs. fire-and-forget batch).

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Receipt Synthesis Batch                                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Sample count: [1000]                                                   │
│                                                                         │
│  Template distribution:                                                 │
│    thermal_minimal      ███████░░░  40%                                 │
│    restaurant_tip       ████░░░░░░  20%                                 │
│    retail_multicol      ██████░░░░  30%                                 │
│    a4_invoice           ██░░░░░░░░  10%                                 │
│                                                                         │
│  Parameter sampler:                                                     │
│    seed_range:          [0, 1000000]                                    │
│    augraphy_preset:     uniform({light, medium, heavy})                 │
│    (v0.3+) hdri:        uniform(50 Poly Haven indoor)                   │
│    (v0.3+) paper_curl:  Sobol([0.0, 0.3])                               │
│                                                                         │
│  [Start batch]                                                          │
│                                                                         │
├──── Job progress ───────────────────────────────────────────────────────┤
│                                                                         │
│   456 / 1000 done   12 failed   ████████░░░░░░ 45%   est 4m 12s remain  │
│                                                                         │
│   [Live preview: random sample updates every ~5s]                       │
│   [Download manifest.jsonl]                                             │
│   [Download dataset.zip] (when complete)                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

Reuses the existing `JobStatusResponse` polling pattern from FDD #25.

---

## 7. What is *not* in this design

- **Editable HTML templates in the UI** — too much complexity for v1.0. Templates are author-time, not user-time. v1.1+ if needed.
- **3D viewport (Three.js / R3F)** — discarded per plan §4 ("server-rendered PNG thumbnail is canonical"). The renderer-parity tradeoff is not worth a Three.js viewer that lies about lighting.
- **OCR running inside the UI** — explicitly out of scope per the v0.1 scope split. When an OCR consumer is selected, that becomes its own page (probably extending the existing `/ocr` page).
- **Real-time slider-driven re-render** — per plan §2, bpy renders are 800ms+ and sliders firing on every drag is unusable. Always use "Render Preview" button.

---

## 8. Phase ↔ UI delivery summary

| Phase | UI surface added | Backend endpoints added |
|---|---|---|
| **v0.2** | NavBar entry + `ReceiptSynthesis` page + stage strip with Content/Raster/Augraphy/Final cards (3D + Camera FX cards visible but disabled). Bbox overlay toggle. Token list. Hand-written parameter form. | `POST /render`, `GET /templates`, `GET /augraphy-presets` |
| **v0.3** | 3D card activates. Stage selector dropdown (any `CoordSnapshot` stage drawable on the 3D image). HDRI thumbnail picker. | `GET /hdri-thumbnails`, `StageOutput.stage` extended |
| **v0.4** | New `/receipt-synthesis/batch` page. Job-progress poller. | `POST /batch`, `GET /batch/{id}`, `GET /batch/{id}/download` |
| **v1.0** | Camera FX card activates. Contact-sheet page (`/receipt-synthesis/contact-sheet`). | `POST /contact-sheet`, `StageOutput.stage` extended |

---

## 9. Acceptance check

After all phases ship, a non-developer should be able to, in the React webapp:
1. Pick a template from a dropdown
2. Click "Render Preview"
3. See the receipt content, the rendered receipt, the degraded receipt, the 3D photo, and the final phone-photo-with-FX as five cards
4. Click any card to see the bbox overlay for that stage's image
5. Tweak any single parameter (e.g. lighting HDRI) and re-render *only* the downstream stages
6. Switch to the batch page, configure 10k samples, hit Start, watch progress, download the dataset
7. Throughout: never need to read code, never need to edit JSON by hand

That's the bar.
