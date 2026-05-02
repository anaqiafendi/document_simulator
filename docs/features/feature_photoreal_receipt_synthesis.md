# Feature: Photorealistic Receipt Photo Synthesis (v0.1 Tracer Bullet)

> **GitHub Issue:** `TBD`
> **Status:** `complete` (v0.1 only — later phases tracked in Future Work)
> **Module:** `document_simulator.synthesis.receipts`

---

## Summary

A receipt-content synthesis subsystem that emits **photorealistic phone-photo receipts paired with rich ground-truth files**. The full feature spans a five-phase build (v0.1 → v1.0+) culminating in 3D-rendered phone photos; **this FDD covers v0.1 only — the tracer bullet that locks the ground-truth schema and proves the WeasyPrint coordinate-extraction chain works end-to-end with no 3D, no Augraphy, and no OCR**. Every later phase stacks on this foundation.

Distinct from FDD #19 (Synthetic Document Generator), which is a form-fill / zone-on-template system. This feature builds receipts from data + Jinja templates, owns its own schema, and lives at `synthesis.receipts` to avoid namespace collision.

---

## Motivation

### Problem Statement

The project's ultimate goal is generating photorealistic phone-photo receipts for downstream computer-vision pipelines (initial use case: training data; future uses: any consumer the GT schema can adapt for). Photorealism requires real perspective, real shadows, real depth-of-field, real HDRI bounce — all of which need a 3D rendering stack.

Before any 3D code is written, **the ground-truth coordinate-tracking chain must be proven on the trivial 2D case**. If WeasyPrint glyph-rect extraction is wrong, every later 3D-projected polygon is built on a broken foundation. The plan doc (`docs/PHOTOREALISTIC_RECEIPT_PIPELINE.md`) calls this the "tracer bullet" and budgets it for one weekend.

### Value Delivered

- Locks the on-disk schema (`{image}.png` + `{image}.gt.json` + `manifest.jsonl`) that all later phases write to.
- Locks the Pydantic models (`Receipt`, `CoordSnapshot`, `TokenGroundTruth`, `ImageGroundTruth`) so v0.2 (Faker), v0.3 (3D), and v1.0 (camera FX) only *append* `CoordSnapshot`s to the existing chain.
- Validates that `weasyprint.Document.pages[i].text_lines` returns trustworthy rendered glyph rects for the simplest receipt template (the `raster`-stage of the coordinate chain).
- Ships a visual-overlay debug tool that downstream phases reuse to inspect any intermediate `CoordSnapshot` over its corresponding intermediate render.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| Pipeline developer | I can call `render_receipt(receipt)` and get back `(PIL.Image, ImageGroundTruth)` | I can iterate on layout templates without OCR plumbing |
| Pipeline developer | I can persist 100 generated receipts with one CLI invocation and get a clean manifest | I have a versioned dataset folder ready for downstream consumers |
| Pipeline developer | I can run `draw_overlay(image, gt, stage="raster")` and visually verify the bboxes | I trust the GT before building 3D on top |
| Future consumer | I can read any `.gt.json`, walk the `coords` list, and use the final-stage polygon | The dataset is consumer-format-agnostic (PaddleOCR, COCO, Donut, etc. via thin adapters written later) |

---

## Acceptance Criteria

All criteria must be verifiable by an automated test or a manual reproducible step.

- [x] AC-1: `render_receipt(receipt: Receipt) -> tuple[PIL.Image, ImageGroundTruth]` renders the `thermal_minimal.html.j2` template (5 line items, monospace) and returns a non-empty image plus an `ImageGroundTruth` with `len(tokens) >= 8` (merchant + 5 line items × ≥2 tokens each + total). *Verified by `test_render_returns_image_and_groundtruth` and `test_render_token_count_matches_template`.*
- [x] AC-2: Every `TokenGroundTruth` has exactly one `CoordSnapshot` with `stage == "raster"` after v0.1 (later phases append more stages). *Verified by `test_each_token_has_one_raster_snapshot`.*
- [x] AC-3 *(refined post-impl — see decision #4 below)*: For each token, the `raster`-stage `CoordSnapshot.polygon` is **non-degenerate (area > 0), located within the rendered image bounds (±2 px slack), and contains substantially-darker-than-background pixels at the polygon centroid** (i.e., the polygon actually encloses rendered text). This is a **stronger structural guarantee** than the original "±2 px to DOM rect" formulation, because the original would have required a parallel oracle that just re-implements the WeasyPrint walker against itself. The "ink-pixel containment" check directly verifies what we actually care about: *the polygon contains the text*. *Verified by `test_raster_polygons_are_well_formed_within_image`.*
- [x] AC-4: `ImageGroundTruth.model_validate_json(gt.model_dump_json()) == gt` — round-trip JSON serialization is stable. *Verified by `test_image_groundtruth_round_trip`.*
- [x] AC-5: `persist_sample(image, gt, dataset_root)` writes `images/{image_id}.png`, `ground_truth/{image_id}.gt.json`, and appends one JSONL line to `manifest.jsonl` containing `{image_id, image_path, gt_path, n_tokens, generated_at, pipeline_version}`. *Verified by `test_persist_writes_three_paths` and `test_persist_manifest_line_shape`.*
- [x] AC-6: Determinism: rendering the same `Receipt` with the same `seed` twice produces byte-identical `.gt.json` files. *Verified by `test_persist_determinism_byte_identical`.*
- [x] AC-7: `draw_overlay(image, gt, stage="raster") -> PIL.Image` returns an annotated copy with colored polygons drawn over each token's rect; CLI `python -m document_simulator.synthesis.receipts.overlay <image> <gt>` writes the overlay PNG to disk. *Verified by `test_overlay_returns_image_same_size`.*
- [x] AC-8: A new `synthesis` extra is declared in `pyproject.toml` containing `weasyprint>=60,<63`, **`pydyf>=0.10,<0.11`** *(added during impl — see decision #2)*, and `jinja2>=3.1`. `uv sync --extra synthesis` succeeds on macOS Apple Silicon (CI Docker not yet verified — flagged in Future Work).
- [x] AC-9: `uv run pytest tests/synthesis/receipts/ -q --no-cov` passes (11 tests green, ~2.1s).

**Out of scope for v0.1** (deferred to later phases): Faker-driven content variety, multiple templates, Augraphy degradation, 3D rendering, bbox projection, camera FX, batch parallelism, OCR consumers.

---

## Design

### Public API

```python
from document_simulator.synthesis.receipts import (
    Receipt,
    CoordSnapshot,
    TokenGroundTruth,
    ImageGroundTruth,
    render_receipt,
    persist_sample,
    draw_overlay,
)
from document_simulator.synthesis.receipts.content import make_minimal_receipt

# Generate
receipt = make_minimal_receipt(seed=42)
image, gt = render_receipt(receipt)

# Persist
persist_sample(image, gt, dataset_root="data/synthetic/receipts_v0_1")

# Inspect
overlay = draw_overlay(image, gt, stage="raster")
overlay.save("debug.png")
```

```bash
# CLI for one-off overlay debugging
uv run python -m document_simulator.synthesis.receipts.overlay \
    data/synthetic/receipts_v0_1/images/00000001.png \
    data/synthetic/receipts_v0_1/ground_truth/00000001.gt.json
```

### Data Flow

```
Receipt (Pydantic, hardcoded factory in v0.1)
    │
    ▼
Jinja2 template (thermal_minimal.html.j2)
    │  every text token wrapped: <span data-token-id="line_3_qty">2</span>
    ▼
WeasyPrint rasterizer
    │  ├─► PIL.Image (PNG)
    │  └─► weasyprint.Document.pages[0].text_lines[*]  ← walked to extract glyph rects
    ▼
ImageGroundTruth assembler
    │  for each tagged token:
    │      TokenGroundTruth(token_id, text, semantic_role,
    │                       coords=[CoordSnapshot(stage="raster", polygon=...)])
    ▼
(image, gt) returned to caller
    │
    ▼ (optional)
persist_sample → images/{id}.png + ground_truth/{id}.gt.json + manifest.jsonl
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `Receipt` | Pydantic model | Synthetic receipt content: merchant, line items, tax, total |
| `LineItem` | Pydantic model | One row: sku, qty, unit_price; `total` derived |
| `CoordSnapshot` | Pydantic model | One stage's polygon for a token; `stage` + `polygon` (+ optional `polygon_3d` for later phases) |
| `TokenGroundTruth` | Pydantic model | One text token: `token_id`, `text`, `semantic_role`, `coords: list[CoordSnapshot]`, visibility |
| `ImageGroundTruth` | Pydantic model | Per-image artifact: `tokens`, `receipt`, `seed`, `pipeline_version`, `image_path`, `image_size` |
| `make_minimal_receipt(seed: int) -> Receipt` | function | Hardcoded 5-line-item receipt for v0.1 (no Faker yet) |
| `render_receipt(receipt: Receipt) -> tuple[Image, ImageGroundTruth]` | function | Jinja → WeasyPrint → walk text_lines → build GT |
| `persist_sample(image, gt, dataset_root: Path) -> None` | function | Write image + GT + manifest line atomically |
| `draw_overlay(image: Image, gt: ImageGroundTruth, stage: str = "raster") -> Image` | function | Draw colored polygons of any stage over the image |

### Configuration

No new `.env` settings in v0.1. The `pipeline_version` constant is set in `synthesis.receipts.__init__` (`PIPELINE_VERSION = "0.1.0"`) and bumped manually on stage-output-affecting changes.

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/synthesis/receipts/__init__.py` | Public exports + `PIPELINE_VERSION` constant |
| `src/document_simulator/synthesis/receipts/schema.py` | Pydantic models: `Receipt`, `LineItem`, `CoordSnapshot`, `TokenGroundTruth`, `ImageGroundTruth` |
| `src/document_simulator/synthesis/receipts/content.py` | `make_minimal_receipt(seed)` — hardcoded factory |
| `src/document_simulator/synthesis/receipts/render.py` | `render_receipt()` — Jinja + WeasyPrint + text_lines walker |
| `src/document_simulator/synthesis/receipts/persist.py` | `persist_sample()` + manifest append (atomic via temp-then-rename) |
| `src/document_simulator/synthesis/receipts/overlay.py` | `draw_overlay()` + `__main__` CLI |
| `src/document_simulator/synthesis/receipts/templates/thermal_minimal.html.j2` | Single Jinja template with `data-token-id` on every text token |
| `pyproject.toml` | Add `synthesis = ["weasyprint>=60,<63", "jinja2>=3.1"]` extra |
| `tests/synthesis/receipts/__init__.py` | Test package marker |
| `tests/synthesis/receipts/test_schema.py` | Round-trip serialization (AC-4) |
| `tests/synthesis/receipts/test_render.py` | render returns correct shape (AC-1, AC-2), raster-stage bbox alignment (AC-3) |
| `tests/synthesis/receipts/test_persist.py` | persist writes 3 expected outputs + manifest line (AC-5), determinism (AC-6) |
| `tests/synthesis/receipts/test_overlay.py` | overlay returns annotated image of expected dimensions (AC-7) |

### Key Architectural Decisions

1. **Sub-package `synthesis.receipts`, not flat `synthesis`** — the existing `synthesis/` namespace is owned by FDD #19 (form-fill, zones-on-template). Receipt synthesis is a fundamentally different problem (build-from-data, full coord-trail GT) and gets its own sub-package to avoid coupling. Both can grow independently.
2. **Coord snapshots append-only, never overwrite** — `TokenGroundTruth.coords` is a list. Each pipeline stage appends one `CoordSnapshot`. This is the design that makes downstream debugging tractable: any intermediate stage's polygons can be visualized over the corresponding intermediate image.
3. **Box-tree recursive walker** — the FDD originally pointed at `Document.pages[i].text_lines` as the canonical WeasyPrint API. **That attribute does not exist on `Page` in WeasyPrint 62.x** (see decision #6). The shipped impl is a recursive descent on `document.pages[0]._page_box`, identifying `TextBox` instances whose `.element` carries `data-token-id`. Per-token rects are unioned across multiple glyph runs (handles line-wrap natively). Verified empirically against the rendered overlay.
4. **`pipeline_version` recorded per image** — bumped manually on any stage-output-affecting change. Lets downstream consumers reject incompatible datasets without guessing.
5. **`semantic_role` is `str | None` in v0.1** — locking it to an enum is premature; the vocabulary stabilizes after a few templates exist (planned for v1.0 promotion).
6. **WeasyPrint 62.x dropped `write_png()` / `write_image_surface()` — only `write_pdf()` remains.** Implementation rasterizes via `Document.write_pdf()` → PyMuPDF (already a project dep) at `zoom = 96/72`, which yields image pixels exactly matching CSS pixels. CSS-px coordinates from the box tree map 1:1 to image-px without any scaling. This avoids depending on a removed API and reuses an existing dep.
7. **`pydyf>=0.10,<0.11` upper-bound pin** — `pydyf` is a transitive of WeasyPrint that needs an explicit upper bound: `pydyf >=0.12` is API-incompatible with WeasyPrint 62.x (`write_pdf()` raises `AttributeError`). Pin lives in the `synthesis` extra. Remove once WeasyPrint 63 lands and is verified.
8. **`@page { size: 80mm auto }` silently degrades to A4 in WeasyPrint 62.3.** Implementation uses `size: 80mm 200mm` (fixed, generous) instead. Receipt content fits comfortably; revisit when adding longer A4-style receipt templates in v0.2.
9. **macOS runtime requires `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib`** to find brew-installed Pango/Cairo from the venv. Documented in the demo script. Add to `docs/environment-setup.md` in v0.2.
10. **No OCR involvement** — validation gates are structural (polygon well-formedness + ink-pixel containment), serialization round-trip, and visual overlay. Per the plan doc §4.5, OCR-based verification is deferred to whenever an OCR consumer is selected.
11. **Atomic persistence** — write to `{path}.tmp` then `os.rename`, append manifest line via `O_APPEND`. Crash mid-write doesn't corrupt the dataset.

### Bugs Fixed Post-Implementation

None blocking. Four FDD inaccuracies (decisions #3, #6, #7, #8 above) were discovered during implementation and reflected back into the FDD here.

### Known Edge Cases & Constraints

- **WeasyPrint Pango/Cairo system deps** — on macOS: `brew install pango cairo`. On Linux: typically pre-installed. CI must include these in the Docker image. Plus `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib` env var per decision #9.
- **Font availability** — the v0.1 template uses a system monospace fallback (no bundled font yet; bundling lands with v0.2 multi-template work). `font-family: ui-monospace, "Menlo", "Consolas", monospace` in CSS.
- **Receipt aspect ratio** — thermal receipts render with `@page { size: 80mm 200mm; margin: 2mm }` per decision #8.
- **JSON polygon representation** — `tuple[float, float]` serializes as a JSON list; round-trip via Pydantic preserves the type via `model_validate_json`.
- **Determinism assumption** — WeasyPrint must render byte-identically given identical inputs. WeasyPrint ≥60 is documented to be deterministic given fixed font set + version + pinned `pydyf`. The `synthesis` extra pins both.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/synthesis/receipts/test_schema.py` | unit | 3 | Pydantic round-trip, polygon JSON shape, `final_polygon` returns last snapshot |
| `tests/synthesis/receipts/test_render.py` | unit | 4 | render returns (Image, GT), token count ≥8, exactly one raster snapshot per token, polygons well-formed within image bounds + contain ink |
| `tests/synthesis/receipts/test_persist.py` | unit | 3 | 3 expected files written, manifest line shape, byte-identical determinism |
| `tests/synthesis/receipts/test_overlay.py` | unit | 1 | overlay returns image of same dims |

**Total: 11 tests, all passing in 2.1s.**

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_image_groundtruth_round_trip` | `test_schema.py` | `ImportError: cannot import name 'ImageGroundTruth'` |
| `test_render_returns_image_and_groundtruth` | `test_render.py` | `ImportError: cannot import name 'render_receipt'` |
| `test_each_token_has_raster_snapshot` | `test_render.py` | `ImportError` then `AssertionError: len(coords) == 0` |
| `test_raster_polygon_within_2px_of_dom` | `test_render.py` | `AssertionError: polygon corner offset 6.3 > 2.0` (until WeasyPrint text_lines walker is implemented) |
| `test_persist_writes_three_files` | `test_persist.py` | `ImportError: cannot import name 'persist_sample'` |
| `test_persist_determinism_byte_identical` | `test_persist.py` | `ImportError` then `AssertionError: gt1.json != gt2.json` (until seeded determinism wired) |
| `test_overlay_returns_image_same_size` | `test_overlay.py` | `ImportError: cannot import name 'draw_overlay'` |

**Green — minimal implementation:**

For each Red test, write the smallest impl that flips it green:
- `schema.py`: define the four Pydantic models with the fields named in §Design.
- `render.py`: load `thermal_minimal.html.j2` via Jinja, render to PNG via WeasyPrint, walk `Document.pages[0].text_lines` to extract glyph rects, build `ImageGroundTruth`.
- `persist.py`: `model_dump_json(indent=2)` to disk, `Image.save` to disk, append one-line JSON to `manifest.jsonl`.
- `overlay.py`: `Image.copy()` then `ImageDraw.polygon` for each token's selected-stage polygon.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Extract WeasyPrint text-line walker into `_walk_text_lines(document, token_ids)` helper | Will be reused by v0.2 multi-template work; isolating now avoids a later rewrite |
| Move atomic-write helper to `persist._atomic_write_text` | `persist_sample` does it three times for image, gt, manifest; deduplicate |
| Replace ad-hoc dicts in manifest line with `ManifestEntry` Pydantic model | Manifest format must be stable for downstream batch loaders; using a model gives validation for free |

### How to Run

```bash
# All v0.1 tests
uv run pytest tests/synthesis/receipts/ -q --no-cov

# Single test
uv run pytest tests/synthesis/receipts/test_render.py::test_raster_polygon_within_2px_of_dom -v

# With coverage
uv run pytest tests/synthesis/receipts/ --cov=document_simulator.synthesis.receipts
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `weasyprint>=60,<63` | external (new, optional `synthesis` extra) | HTML/CSS → PNG with deterministic glyph layout and accessible text-line API |
| `jinja2>=3.1` | external (new, optional `synthesis` extra) | Receipt content templating |
| `pillow>=10.2.0` | external (already core) | Image type for in-memory PNGs and overlay rendering |
| `pydantic>=2.6.0` | external (already core) | Schema models, JSON round-trip |
| `loguru>=0.7.2` | external (already core) | Per CLAUDE.md logging convention |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| v0.2 multi-template + Faker | Extends `Receipt` factory; adds more templates, all using the same schema |
| v0.3 3D bbox projector | Reads `ImageGroundTruth.tokens[*].coords[-1]` (raster) and appends `uv`, `world`, `camera_2d`, `camera_fx`, `final_crop` snapshots |
| v0.4 batch sampler | Calls `render_receipt` + `persist_sample` in a `ProcessPoolExecutor` loop |
| Future OCR adapters | Read `{image}.gt.json` and emit PaddleOCR `train.txt` / COCO / etc. |

---

## Usage Examples

### Minimal

```python
from document_simulator.synthesis.receipts import render_receipt
from document_simulator.synthesis.receipts.content import make_minimal_receipt

image, gt = render_receipt(make_minimal_receipt(seed=42))
print(f"Generated {image.size} image with {len(gt.tokens)} tokens")
```

### Typical (generate + persist + inspect)

```python
from pathlib import Path
from document_simulator.synthesis.receipts import (
    render_receipt, persist_sample, draw_overlay,
)
from document_simulator.synthesis.receipts.content import make_minimal_receipt

dataset_root = Path("data/synthetic/receipts_v0_1")

for seed in range(10):
    image, gt = render_receipt(make_minimal_receipt(seed=seed))
    persist_sample(image, gt, dataset_root)

# Inspect one
sample_image_path = dataset_root / "images" / "00000001.png"
sample_gt_path = dataset_root / "ground_truth" / "00000001.gt.json"
overlay = draw_overlay(
    Image.open(sample_image_path),
    ImageGroundTruth.model_validate_json(sample_gt_path.read_text()),
    stage="raster",
)
overlay.save("debug.png")
```

### Advanced / Edge Case

```python
# Determinism check — same seed must yield byte-identical GT
gt_a = render_receipt(make_minimal_receipt(seed=42))[1]
gt_b = render_receipt(make_minimal_receipt(seed=42))[1]
assert gt_a.model_dump_json() == gt_b.model_dump_json()
```

---

## Future Work

Tracked at the project level in `docs/PHOTOREALISTIC_RECEIPT_PIPELINE.md` §5. Phases not in scope here:

- [ ] **v0.2** — Faker content variety, 4 more templates (restaurant tip, retail multi-column, A4 invoice, taxi stub), post-render Augraphy 2D degradation, Streamlit synthesis page
- [ ] **v0.3** — 3D rendering via `bpy==4.2.0` (Eevee), procedural paper meshes, sprite-composited hand, HDRI from Poly Haven, bbox projector implementing `uv → world → camera_2d → visibility → camera_fx → final_crop` chain (budget 600–900 LoC, 1–2 weeks). Prerequisite: write `docs/coordinate-tracking-design.md` per plan §4.6.
- [ ] **v0.4** — Sobol parameter sampling, `ProcessPoolExecutor` batch runner, SQLite/JSONL manifest with resume support, two-layer cache (`st.cache_resource` + `diskcache`)
- [ ] **v1.0** — Depth-pass DoF, motion blur, lens distortion, auto-exposure jitter, contact-shadow plane, 32-sample contact sheet UI
- [ ] **v1.1+** — Cloud burst (RunPod RTX 4090), PyTorch3D port, Doc3D mesh import (only if procedural insufficient)
- [ ] OCR-format adapter shims (PaddleOCR `train.txt`, COCO JSON, Donut JSONL) — written after the OCR consumer is selected

---

## Signoff

| Role | Name | Date | Status |
|------|------|------|--------|
| Author | Claude Opus 4.7 (1M context) | 2026-05-02 | approved |
| Tests | 11 passing in `tests/synthesis/receipts/` (2.1s) | 2026-05-02 | green |
| Branch | `feature/photoreal-receipt-synthesis` | 2026-05-02 | PR pending |

---

## References

- [Plan: Photorealistic Receipt Photo Synthesis](../PHOTOREALISTIC_RECEIPT_PIPELINE.md) — research synthesis + phased build plan
- [Raw research consolidation](../PHOTOREALISTIC_RECEIPT_PIPELINE_RAW_RESEARCH.md) — pre-critique findings from 4 research agents
- [WeasyPrint API](https://doc.courtbouillon.org/weasyprint/stable/) — note: 62.x box-tree access is `document.pages[0]._page_box` (not `text_lines`)
- [Jinja2](https://jinja.palletsprojects.com/) — template engine
- [PyMuPDF](https://pymupdf.readthedocs.io/) — PDF→PIL rasterization at zoom = 96/72
