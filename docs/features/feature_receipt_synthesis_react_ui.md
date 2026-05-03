# Feature: Receipt Synthesis — React UI + Faker + Augraphy Wire-In (v0.2)

> **GitHub Issue:** `TBD`
> **Status:** `complete`
> **Module:** `document_simulator.synthesis.receipts` + `document_simulator.api.routers.receipt_synthesis` + `webapp/src/pages/ReceiptSynthesis.tsx`

---

## Summary

Phase v0.2 of the photorealistic receipt synthesis pipeline. Builds on the v0.1 tracer bullet (FDD #27) with: **Faker-backed content variety**, **4 additional receipt templates**, **post-render Augraphy degradation wire-in** (no GT impact — pixel-only ops), a **new FastAPI router** exposing the render pipeline, and the **first React page** in the webapp (`/receipt-synthesis`) implementing the **stage-strip** layout from `docs/PHOTOREAL_RECEIPT_UI_DESIGN.md`.

**Out of scope** (deferred to later phases): 3D rendering, bbox projector, batch generation, photoreal camera FX, OCR consumers. The 3D and Camera FX cards in the UI render as visible-but-disabled placeholders so later phases just populate existing surface.

---

## Motivation

### Problem Statement

v0.1 ships a hardcoded single-template renderer with no UI. To validate that the GT chain holds across template variety + Augraphy degradation — and to give the user a visual interface for inspecting it — we need:

- **Variety**: realistic content distribution (multiple merchants, plausible SKU items, locale-appropriate tax rates) and 5 receipt classes (thermal single-column, restaurant tip, retail multi-column, A4 invoice, taxi stub)
- **Degradation that doesn't break GT**: Augraphy ink/paper/post pipeline applied *after* the raster step, in 2D pixel space, so polygons stay valid (per plan §4.3)
- **Visibility**: a UI surface where the user can pick a template, hit "Render Preview", and see every pipeline stage's output with bboxes overlaid

### Value Delivered

- Generate realistically varied receipts with proper tax/total arithmetic.
- Validate that Augraphy degradation does not corrupt token GT polygons (since it's pure-2D pixel ops post-raster).
- Establish the React UI surface that v0.3 (3D), v0.4 (batch), and v1.0 (camera FX) will populate.
- Lock the FastAPI router shape so frontend ↔ backend contracts are stable across later phases.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| Pipeline developer | I open `/receipt-synthesis` in the React webapp, pick a template, hit Render Preview | I see a synthetic receipt with my exact parameters in <2s |
| Pipeline developer | I toggle "Show bboxes" on the Raster stage card | I visually verify token polygons match rendered text — no need to write a script |
| Pipeline developer | I switch the Augraphy preset from `light` to `heavy` and re-render | I see the visual degradation but the GT polygons stay aligned to the original text |
| Pipeline developer | I select a different template from the dropdown | The render switches to a restaurant-tip layout and the token list updates |
| API consumer (CLI / batch v0.4) | I `POST /api/receipt-synthesis/render` with `{template, seed, augraphy_preset}` | I get back base64 PNGs for each stage + a full `ImageGroundTruth` JSON |

---

## Acceptance Criteria

### Backend

- [x] AC-1: `synthesis.receipts.content.make_receipt(seed, template)` returns a Faker-driven `Receipt` with locale-consistent merchant, address, tax rate, and 3–10 line items with arithmetic-consistent subtotal/tax/total.
- [x] AC-2: 4 new templates exist: `restaurant_tip.html.j2`, `retail_multicol.html.j2`, `a4_invoice.html.j2`, `taxi_stub.html.j2`. Each renders without errors and emits at least 8 tagged tokens.
- [x] AC-3: `synthesis.receipts.augraphy_pretreat.apply_post_render(image: PIL.Image, preset: str) -> PIL.Image` exists, applies the named Augraphy preset, returns a same-size image. **Does not modify the GT** (pixel-only ops).
- [x] AC-4: `POST /api/receipt-synthesis/render` accepts `{template, seed, augraphy_preset?, start_stage?, cached_image_id?}` and returns `{image_id, final_image_b64, ground_truth, stages: [{stage, image_b64, parameters, elapsed_ms}], pipeline_version}`. Response Pydantic models live in `src/document_simulator/api/models.py`.
- [x] AC-5: `GET /api/receipt-synthesis/templates` returns `{templates: [{id, name, description, sample_token_count}]}` for all 5 templates (thermal_minimal + 4 new).
- [x] AC-6: `GET /api/receipt-synthesis/augraphy-presets` returns `{presets: ["light", "medium", "heavy"]}` (these map to the existing `augmentation/presets.py` configurations).
- [x] AC-7: All new tests under `tests/synthesis/receipts/` and `tests/api/routers/test_receipt_synthesis.py` pass: `uv run pytest tests/synthesis/receipts/ tests/api/routers/test_receipt_synthesis.py -q --no-cov`.
- [x] AC-8: Determinism preserved: same `(template, seed, augraphy_preset)` triple → byte-identical `gt.json` and *visually identical* PNG (Augraphy with seeded RNG).

### Frontend

- [x] AC-9: `webapp/src/pages/ReceiptSynthesis.tsx` is registered at `/receipt-synthesis` in `App.tsx` and appears in `NavBar.tsx` as `🧾 Receipt Synthesis`.
- [x] AC-10: The page shows a horizontal stage-strip with 6 cards: Content, Raster, Augraphy, 3D Scene, Camera FX, Final. The 3D Scene and Camera FX cards render as **visible but disabled placeholders** (greyed out, "Coming in v0.3 / v1.0" tooltip).
- [x] AC-11: Top controls expose: template dropdown (5 options), seed input + reroll button, Augraphy preset dropdown, **Render Preview button**.
- [x] AC-12: Clicking a stage card opens an inspector panel below showing the stage's image, a **Show bboxes** toggle, a **Show token labels** toggle, and a token-list table (token_id, text, semantic_role).
- [x] AC-13: The bbox overlay is **client-side SVG** drawn over the `<img>` element. Toggling does not trigger any backend call.
- [x] AC-14: The page handles errors gracefully: render failures show a non-modal banner with the error message; the UI does not crash.
- [x] AC-15: A new `useReceiptSynthesis()` hook in `webapp/src/hooks/` owns the page state (current request, last response, selected stage, overlay flags, isRendering, error).
- [x] AC-16: Type-safe `renderReceipt()` and `listTemplates()` / `listAugraphyPresets()` functions exist in `webapp/src/api/client.ts`. TypeScript types in `webapp/src/types/index.ts` mirror the new Pydantic models.

### Integration

- [x] AC-17: Manual demo: starting the FastAPI backend and the React dev server, opening `http://localhost:5173/receipt-synthesis`, selecting `restaurant_tip` + `medium` Augraphy preset + seed `99`, clicking Render Preview yields all four stage images (Content / Raster / Augraphy / Final) and a token list of 12+ tokens.

---

## Design

### Public API

```python
# Backend (synthesis.receipts.*)
from document_simulator.synthesis.receipts.content import make_receipt
from document_simulator.synthesis.receipts.render import render_receipt   # supports template arg
from document_simulator.synthesis.receipts.augraphy_pretreat import apply_post_render

receipt = make_receipt(seed=42, template="restaurant_tip")  # locale-aware Faker
image, gt = render_receipt(receipt, seed=42, template_name="restaurant_tip.html.j2")
degraded = apply_post_render(image, preset="medium")
```

```http
POST /api/receipt-synthesis/render
{ "template": "restaurant_tip", "seed": 42, "augraphy_preset": "medium" }
→ 200 {
    "image_id": "uuid-...",
    "final_image_b64": "iVBORw0...",
    "ground_truth": { ... ImageGroundTruth ... },
    "stages": [
      { "stage": "content", "image_b64": null, "parameters": {...}, "elapsed_ms": 8 },
      { "stage": "raster",  "image_b64": "iVBORw0...", "parameters": {...}, "elapsed_ms": 187 },
      { "stage": "augraphy","image_b64": "iVBORw0...", "parameters": {...}, "elapsed_ms": 432 }
    ],
    "pipeline_version": "0.2.0"
  }

GET /api/receipt-synthesis/templates
→ 200 { "templates": [ { "id": "thermal_minimal", "name": "Thermal Single-Column", ... }, ... ] }

GET /api/receipt-synthesis/augraphy-presets
→ 200 { "presets": ["light", "medium", "heavy"] }
```

### Data Flow

```
React page state (template, seed, preset)
    │  user clicks Render Preview
    ▼
fetch POST /api/receipt-synthesis/render
    │
    ▼
FastAPI router → receipt_synthesis.render_pipeline()
    │
    ├─► make_receipt(seed, template) ──► Receipt
    │       │ elapsed_ms recorded → StageOutput(stage="content")
    │       ▼
    ├─► render_receipt(receipt, template) ──► (Image, ImageGroundTruth)
    │       │ image base64-encoded → StageOutput(stage="raster", image_b64=...)
    │       ▼
    ├─► (if augraphy_preset) apply_post_render(image, preset) ──► degraded Image
    │       │ degraded base64-encoded → StageOutput(stage="augraphy", image_b64=...)
    │       ▼ (GT unchanged — Augraphy is pixel-only here)
    ├─► assemble final_image_b64 (= last stage's output)
    │
    ▼
ReceiptRenderResponse JSON
    │
    ▼
React: setState(response), render PipelineStageStrip with stage cards
       user clicks card → StageInspector shows image + BboxOverlay
```

### Key Interfaces

**Backend:**

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `make_receipt(seed: int, template: str) -> Receipt` | function | Faker-driven content factory; arithmetic-consistent totals |
| `apply_post_render(image: PIL.Image, preset: str) -> PIL.Image` | function | Wraps existing `augmentation.augmenter.DocumentAugmenter`; pixel-only |
| `ReceiptRenderRequest` / `ReceiptRenderResponse` / `StageOutput` | Pydantic models in `api/models.py` | API contract |
| `receipt_synthesis.router` | FastAPI APIRouter | Mounted at `/api/receipt-synthesis` |

**Frontend:**

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `ReceiptSynthesis` | React page component | Top-level: top controls, stage strip, inspector |
| `PipelineStageStrip` | React component | Horizontal strip of stage cards |
| `PipelineStageCard` | React component | One card: thumbnail, label, badge, click-to-select, disabled state |
| `StageInspector` | React component | Image + bbox overlay + token list for selected stage |
| `BboxOverlay` | React component | SVG polygons over `<img>` for any GT stage |
| `TokenList` | React component | Table of tokens with click → highlight on overlay |
| `useReceiptSynthesis` | React hook | Page state owner: request, response, selectedStage, overlay flags |
| `renderReceipt`, `listTemplates`, `listAugraphyPresets` | API client functions | Typed `fetch` wrappers in `webapp/src/api/client.ts` |

### Configuration

No new `.env` settings. The Augraphy preset names (`light`, `medium`, `heavy`) map to existing presets in `src/document_simulator/augmentation/presets.py`.

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/synthesis/receipts/content.py` | Replace `make_minimal_receipt` with Faker-driven `make_receipt(seed, template)` (keep old function as a thin wrapper for back-compat) |
| `src/document_simulator/synthesis/receipts/render.py` | Add `template_name` parameter (default `thermal_minimal.html.j2`); existing walker logic unchanged |
| `src/document_simulator/synthesis/receipts/augraphy_pretreat.py` | NEW — `apply_post_render(image, preset)` wrapper around existing `DocumentAugmenter` |
| `src/document_simulator/synthesis/receipts/templates/restaurant_tip.html.j2` | NEW — restaurant-style with tip line, server name, table number |
| `src/document_simulator/synthesis/receipts/templates/retail_multicol.html.j2` | NEW — Walmart-style 3-column SKU/name/price |
| `src/document_simulator/synthesis/receipts/templates/a4_invoice.html.j2` | NEW — A4 invoice format with header, billing block, item table |
| `src/document_simulator/synthesis/receipts/templates/taxi_stub.html.j2` | NEW — taxi/parking stub format |
| `src/document_simulator/synthesis/receipts/sku_corpora/grocery.json` | NEW — small SKU vocabulary for thermal_minimal / retail_multicol |
| `src/document_simulator/synthesis/receipts/sku_corpora/restaurant.json` | NEW — restaurant items |
| `src/document_simulator/synthesis/receipts/sku_corpora/services.json` | NEW — taxi / parking / services |
| `src/document_simulator/api/models.py` | Add `ReceiptRenderRequest`, `ReceiptRenderResponse`, `StageOutput`, `TemplateInfo`, `AugraphyPresetList` Pydantic models |
| `src/document_simulator/api/routers/receipt_synthesis.py` | NEW — APIRouter with the 3 endpoints |
| `src/document_simulator/api/app.py` | Mount the new router |
| `tests/synthesis/receipts/test_content_faker.py` | NEW — Faker determinism, arithmetic consistency, locale awareness |
| `tests/synthesis/receipts/test_templates.py` | NEW — each of 5 templates renders, emits ≥8 tokens, polygons well-formed |
| `tests/synthesis/receipts/test_augraphy_pretreat.py` | NEW — apply_post_render returns same-size image; deterministic given same seed |
| `tests/api/routers/__init__.py` | NEW (if missing) |
| `tests/api/routers/test_receipt_synthesis.py` | NEW — `TestClient` invocations for the 3 endpoints |
| `webapp/src/pages/ReceiptSynthesis.tsx` | NEW — top-level page |
| `webapp/src/components/receipt-synthesis/PipelineStageStrip.tsx` | NEW |
| `webapp/src/components/receipt-synthesis/PipelineStageCard.tsx` | NEW |
| `webapp/src/components/receipt-synthesis/StageInspector.tsx` | NEW |
| `webapp/src/components/receipt-synthesis/BboxOverlay.tsx` | NEW |
| `webapp/src/components/receipt-synthesis/TokenList.tsx` | NEW |
| `webapp/src/hooks/useReceiptSynthesis.ts` | NEW |
| `webapp/src/api/client.ts` | Extend with `renderReceipt`, `listTemplates`, `listAugraphyPresets` |
| `webapp/src/types/index.ts` | Extend with `ReceiptRenderRequest/Response`, `StageOutput`, `ImageGroundTruth`, `TokenGroundTruth`, `CoordSnapshot` (TS mirrors of Pydantic) |
| `webapp/src/components/NavBar.tsx` | Add `{ to: '/receipt-synthesis', label: 'Receipt Synthesis', emoji: '🧾' }` to `NAV_ITEMS` |
| `webapp/src/App.tsx` | Add `<Route path="/receipt-synthesis" element={<ReceiptSynthesis />} />` |

### Key Architectural Decisions

1. **One `/render` call per preview, all stages returned** — the API returns base64 images for every executed stage, not just final. Stage switching in the UI is instant (state lookup, no fetch). Trades a slightly larger response payload for much better UX. Documented in `PHOTOREAL_RECEIPT_UI_DESIGN.md` §3.
2. **Augraphy applies post-raster, no GT mutation** — the `apply_post_render` function takes a PIL.Image and returns a PIL.Image. It does not touch `ImageGroundTruth`. This honors plan §4.3 (Augraphy is pixel-only at this stage; ink-bleed sits on the photographed image rather than the printed paper).
3. **Templates are author-time, not user-time** — adding a 6th template is a code change, not a UI feature. v1.1+ might add an in-UI template editor; v0.2 ships the 5 templates as files in the package.
4. **SKU corpora as JSON files in the package** — small (~50 SKUs per category), bundled inside `synthesis/receipts/sku_corpora/`, loaded once at module import time. Loaded via `importlib.resources` for proper packaging.
5. **Hand-written React forms (no auto-gen yet)** — only 4-5 parameters total in v0.2. Auto-generation evaluated at v0.3 per UI design §5.
6. **Visible-but-disabled placeholders for v0.3 + v1.0 stages** — surfaces the eventual UI shape early. Prevents nav restructure when later phases ship.
7. **`useReceiptSynthesis` hook owns ALL page state** — sub-components are dumb (props in, callbacks out). Mirrors `usePreviews` / `useGenerate` pattern from FDD #19's React work.
8. **Frontend tests deferred** — the existing webapp doesn't have a React test runner configured. Adding Vitest/RTL is its own scope. v0.2 validates the frontend via the manual integration AC-17. Frontend test framework setup tracked as v0.4 stretch.

### Known Edge Cases & Constraints

- **Augraphy seeded determinism**: the existing `DocumentAugmenter` accepts a seed in its config. We must thread the receipt seed through to ensure same `(template, seed, preset)` → same output.
- **A4 invoice template aspect ratio** is portrait, not the long thermal strip. The renderer must handle `@page { size: A4 }` for that template. Verify the box-tree walker handles multi-page documents (truncate to page 1 if it spills).
- **macOS DYLD requirement** persists from v0.1 — documented in v0.1 demo script.
- **Frontend lacks test runner** — see decision #8.
- **First stage card "Content" has no image** — UI shows an icon + token-count badge instead. The `StageOutput.image_b64` is `null` for the content stage by spec.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/synthesis/receipts/test_content_faker.py` | unit | 4 | Faker determinism, arithmetic consistency, locale awareness, multiple templates produce different content |
| `tests/synthesis/receipts/test_templates.py` | unit | 5 | each of 5 templates renders, ≥8 tokens, polygons well-formed within image bounds |
| `tests/synthesis/receipts/test_augraphy_pretreat.py` | unit | 3 | apply_post_render returns same-size image, GT unchanged, deterministic given seed |
| `tests/api/routers/test_receipt_synthesis.py` | integration | 5 | render endpoint full flow, templates list, augraphy presets list, error handling, start_stage param |

### TDD Cycle Summary

**Red → Green per file**, in this order:
1. `test_content_faker.py` (Faker factory) — drives `content.py` Faker rewrite
2. `test_templates.py` (4 new templates) — drives template HTML files + render-with-template-name support
3. `test_augraphy_pretreat.py` (post-render Augraphy) — drives `augraphy_pretreat.py`
4. `test_receipt_synthesis.py` (API router) — drives `api/routers/receipt_synthesis.py` + `api/models.py`
5. **Frontend** lands after backend is fully green; no automated tests for v0.2 frontend

**Refactor:** extract a `_load_sku_corpus(category)` helper used by all templates; extract a `RenderTimer` context manager for the per-stage `elapsed_ms` instrumentation.

### How to Run

```bash
# Backend tests
DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib uv run pytest \
    tests/synthesis/receipts/ tests/api/routers/test_receipt_synthesis.py \
    -q --no-cov

# Frontend dev server
cd webapp && npm run dev   # http://localhost:5173

# Backend dev server (separate terminal)
DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib \
    uv run uvicorn document_simulator.api.app:app --reload --port 8000

# Manual integration test
open http://localhost:5173/receipt-synthesis
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `synthesis.receipts.*` (FDD #27) | internal | The v0.1 schema + render foundation |
| `augmentation.augmenter.DocumentAugmenter` | internal | Existing Augraphy wrapper, reused for `apply_post_render` |
| `augmentation.presets` | internal | The light/medium/heavy preset definitions |
| `faker>=24.0.0` | external (already core) | Synthetic content |
| FastAPI (already core) | external | Router pattern from FDD #25 |
| React + Vite + React Router (already in webapp) | external | Frontend stack from FDD #25 |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| v0.3 (3D rendering) | Adds a 3D pipeline stage between Augraphy and Final; populates the disabled 3D card; appends `uv` / `world` / `camera_2d` `CoordSnapshot`s |
| v0.4 (batch) | Reuses `make_receipt` + the `/render` endpoint logic in a `ProcessPoolExecutor` worker; adds a separate `/batch` page |
| v1.0 (camera FX) | Populates the disabled Camera FX card; appends `camera_fx` / `final_crop` `CoordSnapshot`s |

---

## Usage Examples

### Minimal (Python API)

```python
from document_simulator.synthesis.receipts.content import make_receipt
from document_simulator.synthesis.receipts.render import render_receipt
from document_simulator.synthesis.receipts.augraphy_pretreat import apply_post_render

receipt = make_receipt(seed=42, template="restaurant_tip")
image, gt = render_receipt(receipt, seed=42, template_name="restaurant_tip.html.j2")
degraded = apply_post_render(image, preset="medium")
degraded.save("demo.png")
```

### Typical (HTTP API)

```bash
curl -X POST http://localhost:8000/api/receipt-synthesis/render \
  -H "Content-Type: application/json" \
  -d '{"template": "thermal_minimal", "seed": 42, "augraphy_preset": "light"}' \
  | jq '.stages[].stage'
# Output:
# "content"
# "raster"
# "augraphy"
```

### Advanced (React UI)

Open `http://localhost:5173/receipt-synthesis`, pick a template, hit Render Preview, click any stage card to inspect.

---

## Future Work

- [ ] **v0.3** — 3D rendering populates the disabled 3D card; bbox projector implements `uv → world → camera_2d → visibility → camera_fx → final_crop` chain
- [ ] **v0.4** — Batch generation page + `ProcessPoolExecutor` runner + manifest resume
- [ ] **v1.0** — Camera FX populates disabled card; contact-sheet review page
- [ ] Frontend test framework (Vitest + RTL) — would let us automate AC-9 through AC-16
- [ ] Pydantic-driven React form auto-generation (`pydantic-to-typescript`) — evaluated in v0.3

---

## Signoff

| Role | Name | Date | Status |
|------|------|------|--------|
| Author | Claude Opus 4.7 (1M context) | 2026-05-03 | approved |
| Tests (backend) | 29 passing in tests/synthesis/receipts/ + tests/api/routers/test_receipt_synthesis.py (7.7s) | 2026-05-03 | green |
| Build (frontend) | `npm run build` clean (TypeScript strict, no warnings) | 2026-05-03 | green |
| Integration (AC-17) | Live backend round-trip: restaurant_tip seed=99 medium → 26 tokens, 333×832, 3 stages, 444KB final | 2026-05-03 | green |
| Branch | `feature/photoreal-receipt-v02` | 2026-05-03 | PR pending |

### Bugs Fixed Post-Implementation

- **`apply_post_render` signature gained `seed: int = 0`** — FDD originally specced only `(image, preset)` but determinism (AC-8) requires reseeding RNG. Router threads `req.seed` through. Reflected back into FDD §Public API.
- **Augraphy seeded via global RNG re-seed**, not via `DocumentAugmenter` config — the existing `DocumentAugmenter` API doesn't expose a seed parameter (FDD assumption was wrong). Verified empirically that `random.seed(seed)` + `np.random.seed(seed)` immediately before pipeline construction yields byte-identical output.
- **Frontend `TemplateInfo` renamed to `TemplateInfoReceipt`** to avoid collision with the existing `TemplateInfo` type used by `SyntheticGenerator` for PDF template uploads. Backend type name unchanged.
- **A4 invoice silently truncates to page 1** — the existing `render.py` already takes `document.pages[0]`, so multi-page A4 invoices lose later pages. Fine for v0.2 since synthetic invoices fit in one page; future longer-invoice support tracked in Future Work.

### Notable Deviations (already in commit messages, repeated here for the FDD record)

- **Templates registry duplicated** in `content._TEMPLATE_REGISTRY` and `routers/receipt_synthesis._TEMPLATES` — they overlap on the id list but carry different concerns (sampling vs HTTP metadata). Could be unified later.
- **`Faker.seed_instance(seed)` per-call** rather than class-method `Faker.seed()` — avoids leaking determinism state between calls.
- **All locales currently `en_US`** — FDD said "locale-consistent" but didn't enumerate. Per-template locale switching is a one-line change in the registry. Tracked in Future Work.
- **Frontend `selectedStage` defaults to `'raster'`** (not `'content'`) — content stage emits no image; defaults to raster gives the user something to look at after the first render.
- **Synthetic frontend `'final'` stage card** — backend `StageOutput.stage` literal does not include `'final'`; the Final card is wired to `response.final_image_b64` and shows the *last executed stage's* parameters. The `'final'` stageId is purely UI-internal.
- **Backend stage names → CoordSnapshot stage names mapper** in `StageInspector.tsx` (`snapshotStageFor`): augraphy stage maps to `'raster'` snapshot since post-render Augraphy is pixel-only and doesn't change polygons (per design doc §1, FDD §Decision-2).

---

## References

- [Plan: Photorealistic Receipt Photo Synthesis](../PHOTOREALISTIC_RECEIPT_PIPELINE.md) — phased build plan
- [UI Exposure Design](../PHOTOREAL_RECEIPT_UI_DESIGN.md) — stage strip layout, API surface, React component tree
- [FDD #27: v0.1 Tracer Bullet](feature_photoreal_receipt_synthesis.md) — schema + foundation this builds on
- [FDD #25: Migrate Streamlit to React SPA](feature_migrate_streamlit_to_react.md) — establishes the React + FastAPI pattern this follows
