# Feature: Photorealistic Receipt Photo Synthesis (v0.1 Tracer Bullet)

> **GitHub Issue:** `TBD`
> **Status:** `in-progress`
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

- [ ] AC-1: `render_receipt(receipt: Receipt) -> tuple[PIL.Image, ImageGroundTruth]` renders the `thermal_minimal.html.j2` template (5 line items, monospace) and returns a non-empty image plus an `ImageGroundTruth` with `len(tokens) >= 8` (merchant + 5 line items × ≥2 tokens each + total).
- [ ] AC-2: Every `TokenGroundTruth` has exactly one `CoordSnapshot` with `stage == "raster"` after v0.1 (later phases append more stages).
- [ ] AC-3: For each token, the `raster`-stage `CoordSnapshot.polygon` overlaps its DOM-declared rect within ±2 px on all four corners. *(Rationale: WeasyPrint's `Document.pages[i].text_lines` gives true rendered glyph rects, accounting for font hinting; ±2 px is the documented hinting tolerance.)*
- [ ] AC-4: `ImageGroundTruth.model_validate_json(gt.model_dump_json()) == gt` — round-trip JSON serialization is stable.
- [ ] AC-5: `persist_sample(image, gt, dataset_root)` writes `images/{image_id}.png`, `ground_truth/{image_id}.gt.json`, and appends one JSONL line to `manifest.jsonl` containing `{image_id, image_path, gt_path, n_tokens, generated_at, pipeline_version}`.
- [ ] AC-6: Determinism: rendering the same `Receipt` with the same `seed` twice produces byte-identical `.gt.json` files.
- [ ] AC-7: `draw_overlay(image, gt, stage="raster") -> PIL.Image` returns an annotated copy with colored polygons drawn over each token's rect; CLI `python -m document_simulator.synthesis.receipts.overlay <image> <gt>` writes the overlay PNG to disk.
- [ ] AC-8: A new `synthesis` extra is declared in `pyproject.toml` containing `weasyprint>=60,<63` and `jinja2>=3.1`. `uv sync --extra synthesis` succeeds on macOS Apple Silicon and Linux/x86 Docker.
- [ ] AC-9: `uv run pytest tests/synthesis/receipts/ -q --no-cov` passes (all v0.1 tests green).

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
3. **WeasyPrint text-line walker, not HTML coordinate trust** — the obvious-but-wrong impl reads `data-bbox` attributes from the HTML. The right impl walks `Document.pages[i].text_lines[j].text_boxes[k]` to get *true rendered* glyph rects after font hinting and line-wrap arithmetic. Without this, AC-3 silently fails by 1–4 px per token.
4. **`pipeline_version` recorded per image** — bumped manually on any stage-output-affecting change. Lets downstream consumers reject incompatible datasets without guessing.
5. **`semantic_role` is `str | None` in v0.1** — locking it to an enum is premature; the vocabulary stabilizes after a few templates exist (planned for v1.0 promotion).
6. **No OCR involvement** — validation gates are structural (±2 px corner-overlap), serialization round-trip, and visual overlay. Per the plan doc §4.5, OCR-based verification is deferred to whenever an OCR consumer is selected.
7. **Atomic persistence** — write to `{path}.tmp` then `os.rename`, append manifest line via `O_APPEND`. Crash mid-write doesn't corrupt the dataset.

### Known Edge Cases & Constraints

- **WeasyPrint Pango/Cairo system deps** — on macOS: `brew install pango`. On Linux: typically pre-installed. CI must include these in the Docker image.
- **Font availability** — the v0.1 template uses a system monospace fallback (no bundled font yet; bundling lands with v0.2 multi-template work). `font-family: ui-monospace, "Menlo", "Consolas", monospace` in CSS.
- **Receipt aspect ratio** — thermal receipts render with `@page { size: 80mm auto; margin: 2mm }` — height grows with content.
- **JSON polygon representation** — `tuple[float, float]` serializes as a JSON list; round-trip via Pydantic preserves the type via `model_validate_json`.
- **Determinism assumption** — WeasyPrint must render byte-identically given identical inputs. WeasyPrint ≥60 is documented to be deterministic given fixed font set and version. Pin `weasyprint>=60,<63` to lock the rasterization behavior.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/synthesis/receipts/test_schema.py` | unit | ~3 | Pydantic round-trip, polygon JSON shape, default values |
| `tests/synthesis/receipts/test_render.py` | unit | ~4 | render returns (Image, GT), token count, raster-stage exists, ±2 px alignment |
| `tests/synthesis/receipts/test_persist.py` | unit | ~3 | 3 expected files written, manifest line shape, determinism (byte-identical .gt.json) |
| `tests/synthesis/receipts/test_overlay.py` | unit | ~2 | overlay returns image of same dims, CLI smoke test |

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

## References

- [Plan: Photorealistic Receipt Photo Synthesis](../PHOTOREALISTIC_RECEIPT_PIPELINE.md) — research synthesis + phased build plan
- [Raw research consolidation](../PHOTOREALISTIC_RECEIPT_PIPELINE_RAW_RESEARCH.md) — pre-critique findings from 4 research agents
- [WeasyPrint API](https://doc.courtbouillon.org/weasyprint/stable/) — particularly `Document.pages[i].text_lines` for glyph rect extraction
- [Jinja2](https://jinja.palletsprojects.com/) — template engine
