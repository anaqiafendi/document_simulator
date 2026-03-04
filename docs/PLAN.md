# Document Simulator — Implementation Plan

## Original Goal

> **Build a document simulator** that can generate variations of images of scanned documents based on inputted samples and modifying values — red teaming for documents — to RL-tune an extraction and OCR model.

---

## Completed Phases

### Phase 1 — Core Augmentation & OCR (Features #1–#6)

| # | Feature | Module | Status |
|---|---------|--------|--------|
| #1 | Augmentation Presets | `augmentation.presets` | ✅ complete |
| #2 | Document Augmenter | `augmentation.augmenter` | ✅ complete |
| #3 | Batch Processing | `augmentation.batch` | ✅ complete |
| #4 | OCR Engine (PaddleOCR 3.x) | `ocr.engine` | ✅ complete |
| #5 | OCR Metrics (CER/WER) | `ocr.metrics` | ✅ complete |
| #6 | Image I/O | `utils.image_io` | ✅ complete |

### Phase 2 — Data, Ground Truth & RL (Features #7–#11)

| # | Feature | Module | Status |
|---|---------|--------|--------|
| #7 | Ground Truth Loading | `data.ground_truth` | ✅ complete |
| #8 | Document Dataset | `data.datasets` | ✅ complete |
| #9 | RL Environment | `rl.environment` | ✅ complete |
| #10 | RL Trainer (PPO) | `rl.trainer` | ✅ complete |
| #11 | Evaluation Framework | `evaluation.evaluator` | ✅ complete |

### Phase 3 — CLI (Feature #12)

| # | Feature | Module | Status |
|---|---------|--------|--------|
| #12 | CLI | `cli` + `__main__` | ✅ complete |

### Phase 4 — Streamlit UI (Features #13–#18)

| # | Feature | Module | Status |
|---|---------|--------|--------|
| #13 | UI Shared Components | `ui.components.*` + `ui.state` | ✅ complete |
| #14 | Augmentation Lab | `ui.pages.01_augmentation_lab` | ✅ complete |
| #15 | OCR Engine Page | `ui.pages.02_ocr_engine` | ✅ complete |
| #16 | Batch Processing Page | `ui.pages.03_batch_processing` | ✅ complete |
| #17 | Evaluation Dashboard | `ui.pages.04_evaluation` | ✅ complete |
| #18 | RL Training Page | `ui.pages.05_rl_training` | ✅ complete |

**Test coverage:** 234 tests, all passing.

---

## Current Pipeline (post-Phase 4)

```
Real scanned documents (input)
    │
    ▼
DocumentAugmenter (Augraphy presets: light / medium / heavy)
    │  BatchAugmenter — parallel processing, ZIP download
    ▼
OCREngine (PaddleOCR 3.x — detect + recognize)
    │  OCR Metrics — CER, WER, confidence
    ▼
Evaluator.evaluate_dataset()
    │  CER/WER bar chart, confidence box plot
    ▼
DocumentEnv (Gymnasium) → RLTrainer (PPO/SB3)
    │  Live reward chart, stop/save/load model
    ▼
Optimised augmentation pipeline
```

Everything in phases 1–4 operates on **existing** document images. You provide scans; the system augments, evaluates, and learns.

---

## Phase 5 — Synthetic Document Generator (Feature #19)

### Motivation

The existing pipeline can only augment images that already exist. To red-team an OCR system against forms it has never seen — with varied handwriting styles, different software fills, multi-person inputs — we need to **manufacture** realistic filled documents from scratch.

### Goal

Build `document_simulator.synthesis`: a subsystem where users:

1. Supply a **template** (blank page, scanned image, or PDF).
2. **Visually define zones** — bounding boxes placed on the template.
3. **Configure each zone** with a Faker data provider, font settings, fill style, and position-jitter parameters.
4. Click **Generate** to produce batches of filled document images, each paired with a `GroundTruth` annotation.

Generated output is a `DocumentDataset`-compatible directory that feeds directly into the existing augmentation → OCR → RL pipeline.

### What It Unlocks

- Unlimited labelled document images without collecting real forms.
- Realistic within-field positioning variation (not pixel jitter on the whole image).
- Multi-person forms: zones grouped by respondent with independent style and data.
- Reproducible datasets: zone configs serialise to JSON.

### Design Overview

```
SynthesisConfig (Pydantic)
    ├── Template       — blank | image | PDF page
    ├── List[ZoneConfig]
    └── GeneratorConfig — batch size, seed, output dir

SyntheticDocumentGenerator
    ├── TemplateLoader       → PIL Image
    ├── ZoneDataSampler      → str (via Faker)
    ├── ZoneRenderer         → PIL canvas with text
    ├── AnnotationBuilder    → GroundTruth JSON
    └── BatchGenerator       → List[(PIL Image, GroundTruth)]
```

**Fill styles:** `form-fill` | `typed` | `handwritten-font` | `stamp`

**New UI page:** `00_synthetic_generator.py` — visual zone editor (streamlit-drawable-canvas) + batch generation controls.

### Module Structure

```
src/document_simulator/synthesis/
├── __init__.py
├── template.py      # TemplateLoader — blank / image / PDF → PIL Image
├── zones.py         # ZoneConfig (Pydantic), ZoneCollection
├── sampler.py       # ZoneDataSampler — Faker text per zone
├── renderer.py      # ZoneRenderer — PIL drawing, jitter, fill styles
├── fonts.py         # FontResolver — category → TTF path
├── generator.py     # SyntheticDocumentGenerator — orchestrator
└── annotation.py    # AnnotationBuilder → GroundTruth + JSON output
```

### Acceptance Criteria

- AC-1: `SyntheticDocumentGenerator(template, zone_config).generate(n=100)` produces 100 image/annotation pairs.
- AC-2: Each annotation is a valid `GroundTruth` readable by `GroundTruthLoader`.
- AC-3: Zone bounding boxes correspond to where text was rendered.
- AC-4: Text content is drawn from the configured Faker provider.
- AC-5: Position jitter distributes text within zone bounds with configurable spread.
- AC-6: At least three fill styles produce visually distinct results.
- AC-7: Zone configuration serialises to/from JSON (round-trip stable).
- AC-8: Streamlit UI allows visual zone placement with a drawable canvas.
- AC-9: Output directories are compatible with `DocumentDataset` without pre-processing.
- AC-10: Multi-respondent zones are supported with independent style and data per group.

### Open Design Questions (to resolve before implementation)

| # | Question | Impact |
|---|----------|--------|
| Q1 | Best Python library for PDF → PIL Image rendering? (`pypdfium2` vs `pdf2image` vs `PyMuPDF`) | Template loading architecture |
| Q2 | Font resolution strategy: bundle TTFs vs system fonts? Which free handwriting/mono fonts to include? | `FontResolver` design |
| Q3 | Which `faker` providers cover typical document fields? Does `faker_file` add value here? | `ZoneDataSampler` implementation |
| Q4 | `streamlit-drawable-canvas` — still maintained and API-stable? Fallback plan? | UI zone editor |
| Q5 | Handwriting font quality: is a Google Font (Caveat, Indie Flower) sufficient, or do we need stroke simulation? | Realism of `handwritten-font` style |
| Q6 | Jitter model: uniform, Gaussian, or truncated Gaussian within zone bounds? | `ZoneRenderer` position jitter |
| Q7 | Existing tools (SynthDog, DocSim, DataSynth) — what can we reuse vs must build? | Build vs reuse decisions |
| Q8 | Multi-respondent correlated fields: how to seed the same Faker identity across zones in one group? | `ZoneDataSampler` group logic |

### Package Candidates

| Package | Purpose | Confidence |
|---------|---------|------------|
| `faker` | Realistic field data | High |
| `faker_file` | File-type fake data | Low — needs research |
| `Pillow` | Canvas rendering | High — already a dep |
| `pypdfium2` | PDF → PIL (no system dep) | Medium |
| `pdf2image` | PDF → PIL (wraps poppler) | Medium |
| `PyMuPDF` (fitz) | Full PDF read/write | Medium — AGPL concern |
| `fpdf2` | PDF generation from scratch | Medium |
| `streamlit-drawable-canvas` | Visual zone editor | Low — stability unknown |
| Google Fonts TTF bundles | Free fonts (handwriting etc.) | High — needs licence check |

### Phase 5 Integration with Existing Pipeline

```
Synthetic Document Generator
    │  output/doc_NNNNNN.png + .json
    ▼
DocumentDataset(output_dir)      ← feature #8
    ▼
DocumentAugmenter("heavy")       ← feature #2
    ▼
OCREngine.recognize()            ← feature #4
    ▼
Evaluator.evaluate_dataset()     ← feature #11
    ▼
RLTrainer (PPO)                  ← feature #10
```

---

## Future Work (Post Phase 5)

- Stroke-based handwriting simulation (pen pressure, speed modelling).
- Checkbox / radio button zone types.
- Signature zone: loop-based glyph generation.
- Multi-page PDF template support.
- AcroForm auto-detection to suggest zone placement from existing PDF forms.
- Export filled PDF (not just PNG) for PDF-native extraction testing.

---

## References

- [RESEARCH_FINDINGS.md](RESEARCH_FINDINGS.md)
- [Feature Index](features/README.md)
- [feature_synthetic_document_generator.md](features/feature_synthetic_document_generator.md)
- [SynthDog — CLOVA AI](https://github.com/clovaai/donut)
- [Faker documentation](https://faker.readthedocs.io/)
