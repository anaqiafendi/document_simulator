# Research Findings: Document Simulator

## Project Overview

This project aims to build a **document simulator** that can:
1. Generate variations of scanned document images based on input samples
2. Modify specific values/fields within documents programmatically
3. Serve as a red teaming tool for testing document extraction and OCR systems
4. Generate synthetic training data for RL tuning of extraction and OCR models

The goal is to create realistic document variations to improve the robustness and accuracy of document processing models.

---

## 1. Document Image Augmentation

### Augraphy (Recommended Primary Tool)
- Python library specifically designed for document image augmentation
- 100+ augmentation effects designed for documents
- Simulates ink, paper, post-processing, and markup effects
- Pipeline-based architecture for combining effects
- Installation: `pip install augraphy`
- GitHub: https://github.com/sparkfish/augraphy

### Albumentations
- General-purpose image augmentation with document-relevant transforms
- Fast performance (uses OpenCV)
- Geometric transforms, color/brightness adjustments, noise and blur
- Installation: `pip install albumentations`
- Documentation: https://albumentations.ai/

### Document-Specific Augmentation Techniques
1. **Geometric**: Perspective distortion, rotation, skew, warping
2. **Degradation**: Paper texture/aging, ink bleeding/fading, watermarks, stains, crumpling
3. **Scanning Artifacts**: Scanner noise, shadows, lighting variations, motion blur, defocus
4. **Post-processing**: JPEG compression, resolution changes, contrast adjustments, binarization

---

## 2. OCR and Document Extraction

### OCR Engines

| Engine | Type | Languages | Best For |
|--------|------|-----------|----------|
| **PaddleOCR** | Deep learning | Multi-language | Best accuracy/speed balance |
| **EasyOCR** | Deep learning | 80+ | Complex layouts |
| **Tesseract** | Traditional + LSTM | 100+ | Baseline comparison |

### Document Understanding Models

- **LayoutLM / LayoutLMv3** (Microsoft) — Combines text, layout, and image; pre-trained on millions of documents; available via Hugging Face
- **Donut** — OCR-free document understanding; end-to-end transformer model
- **TrOCR** — Transformer-based OCR; state-of-the-art text recognition

### Cloud Services (for benchmarking)
- Google Cloud Vision API
- AWS Textract
- Azure Computer Vision / Form Recognizer

---

## 3. Reinforcement Learning for Document Processing

### RL Frameworks

| Framework | Backend | Best For |
|-----------|---------|----------|
| **Stable-Baselines3** | PyTorch | Primary RL framework (well-documented) |
| **Ray RLlib** | Multiple | Large-scale distributed training |
| **TF-Agents** | TensorFlow | TF ecosystem projects |

### RL Problem Formulation
- **State**: Document image + current extraction results
- **Action**: Select regions, adjust parameters, choose extraction methods
- **Reward**: Accuracy of extracted information vs. ground truth
- **Goal**: Learn optimal extraction strategy for various document types

### Training Considerations
- Reward shaping is critical (sparse rewards are challenging)
- May need curriculum learning (start with easy documents)
- Combination with supervised learning likely optimal
- Consider imitation learning from expert extraction rules

---

## 4. Synthetic Document Generation

### Template-Based Generation
- **ReportLab** — Programmatic PDF creation (`pip install reportlab`)
- **Pillow (PIL)** — Image creation, text rendering, format conversion
- **Faker** — Realistic fake data (names, addresses, dates, amounts) (`pip install faker`)
- **python-docx** — Word document generation (`pip install python-docx`)

### Generative AI Approaches
- **Diffusion Models / ControlNet** — Generate realistic document backgrounds/textures
- **GANs** — Learn to generate document-like images (research-level)

---

## 5. Value Modification and Field Replacement

### Approaches

#### OCR + Template Matching
1. Use OCR to locate existing values
2. Identify field types (dates, amounts, names)
3. Replace with synthetic values using similar formatting
4. Re-render with matching fonts and styling

#### Inpainting + Text Rendering
1. Use image inpainting to remove existing text (`cv2.inpaint()`)
2. Render new text with matching font/style (Pillow ImageDraw)
3. For advanced cases: LaMa, Stable Diffusion inpainting

#### PDF Layer Manipulation (for digital documents)
1. Parse PDF text layers (PyPDF2, pdfplumber)
2. Modify text content programmatically
3. Re-render to image (pdf2image)

### Font Matching
- **fontTools** (`pip install fonttools`) — Parse and extract font metrics
- **Pillow + system fonts** — Render text with specific fonts

---

## 6. Data Annotation and Ground Truth

- **Label Studio** — Open-source data labeling with OCR integration (`pip install label-studio`)
- **CVAT** — Annotation tool from Intel, good for bounding boxes
- **VGG Image Annotator (VIA)** — Lightweight browser-based annotation

---

## 7. Recommended Tech Stack

### Core
| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Augmentation | Augraphy, Albumentations |
| Image Processing | Pillow, OpenCV, NumPy |
| OCR | PaddleOCR (primary), Tesseract (baseline) |
| Document Understanding | LayoutLM via Hugging Face Transformers |

### Synthetic Data
| Component | Technology |
|-----------|-----------|
| Fake Data | Faker |
| PDF Generation | ReportLab |
| DOCX Generation | python-docx |

### RL Training
| Component | Technology |
|-----------|-----------|
| RL Framework | Stable-Baselines3 |
| Deep Learning | PyTorch |
| Experiment Tracking | Weights & Biases or MLflow |

### Data Management
| Component | Technology |
|-----------|-----------|
| Annotation | Label Studio |
| Version Control | DVC |
| Metadata Storage | SQLite or PostgreSQL |

---

## 8. Proposed Pipeline

```
1. Template Creation
   - Create base document templates (ReportLab/python-docx)
   - Define field locations and types

2. Value Variation
   - Generate synthetic values (Faker)
   - Modify document fields programmatically

3. Image Augmentation
   - Apply Augraphy augmentation pipeline
   - Generate multiple variations per document
   - Simulate real-world scanning conditions

4. Ground Truth Management
   - Track original values and locations
   - Store metadata (field types, positions, values)

5. RL Training Pipeline
   - Feed augmented documents to extraction model
   - Calculate reward based on extraction accuracy
   - Update RL policy, iterate

6. Evaluation
   - Test on held-out documents
   - Measure extraction accuracy
   - Analyze failure modes
```

---

## 9. Feasibility Assessment

### Technical Feasibility: HIGH

**Strengths:**
- Mature libraries exist for all core components
- Document augmentation is a solved problem (Augraphy)
- OCR technology is production-ready
- RL frameworks are well-established

### Implementation Complexity: MEDIUM

| Component | Estimated Time |
|-----------|---------------|
| Basic augmentation pipeline | 1-2 weeks |
| OCR integration | 1 week |
| Template-based generation | 2 weeks |
| Value modification with font matching | 2-3 weeks |
| RL integration and reward design | 3-4 weeks |
| End-to-end pipeline | 2 weeks |
| **Total MVP** | **8-12 weeks** |

---

## 10. Potential Challenges & Mitigations

| Challenge | Mitigation |
|-----------|-----------|
| Font matching for realistic text replacement | Start with digital PDFs; use deep learning inpainting for complex cases |
| RL reward function design | Start with supervised baseline; use dense per-field rewards |
| Unrealistic augmentations harming training | Use Augraphy (research-validated); validate with domain experts |
| Tracking field locations through augmentations | Use coordinate-aware augmentation; store transformation matrices |
| Scalability (millions of variations) | Parallelize pipeline; use efficient OpenCV processing; cache results |

---

## 11. Alternative Approaches

| Approach | When to Use | Trade-offs |
|----------|-------------|-----------|
| Generative models (GANs/diffusion) | Need entirely novel documents | Higher compute, less controllable |
| Supervised learning (no RL) | Simpler baseline needed | Less adaptive, needs more labeled data |
| Commercial Document AI | Benchmarking only | Cost per doc, vendor lock-in, privacy concerns |
| Active learning + synthetic | Have some real documents | Better generalization, needs human annotation |

---

## 12. MVP Specification (4 Weeks)

**Input:** 10 sample document images + CSV with field values to modify
**Processing:** Generate 100 variations per document (1,000 total)
**Output:** Augmented images + ground truth JSON with field locations and values
**Evaluation:** Run OCR, measure extraction accuracy, compare with baseline

**MVP Stack:** Python 3.10+, Augraphy, Pillow, PaddleOCR, Faker, pandas, matplotlib

---

## 13. References & Resources

### Libraries
- Augraphy: https://github.com/sparkfish/augraphy
- Albumentations: https://albumentations.ai/
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
- EasyOCR: https://github.com/JaidedAI/EasyOCR
- Stable-Baselines3: https://stable-baselines3.readthedocs.io/
- Label Studio: https://labelstud.io/

### Models (Hugging Face)
- LayoutLM: https://huggingface.co/models?search=layoutlm
- Donut: https://huggingface.co/naver-clova-ix/donut-base
- TrOCR: https://huggingface.co/models?search=trocr

### Papers
- "Augraphy: A Data Augmentation Library for Document Images" (2022)
- "LayoutLMv3: Pre-training for Document AI with Unified Text and Image Masking" (2022)
- "Donut: Document Understanding Transformer without OCR" (2022)

---

## Conclusion

This project is highly feasible using existing open-source technologies. The recommended approach is:

1. **Phase 1-3**: Build solid augmentation and extraction pipeline
2. **Phase 4**: Add RL capabilities once foundation is stable
3. **Iterate** based on evaluation metrics

**Key Success Factors:**
- Leverage proven libraries (especially Augraphy)
- Start simple before adding RL complexity
- Build robust ground truth management from the beginning
- Focus on practical, incremental improvements

---

## 2026-03-07 — Multi-Template Batch Augmentation

### Context

This section documents research findings for extending the Batch Processing page
(`src/document_simulator/ui/pages/03_batch_processing.py`) and the underlying
`BatchAugmenter` (`src/document_simulator/augmentation/batch.py`) to support
**multi-template batch augmentation**: given N input document images, generate M
total augmented outputs where each output randomly picks one input as its source template.

---

### 1. Existing `BatchAugmenter` (`augmentation/batch.py`) — Full Analysis

Current interface:

```python
class BatchAugmenter:
    def __init__(self, augmenter="default", num_workers=4, show_progress=False)
    def augment_batch(self, images: List[Image | Path], parallel=True) -> List[Image]
    def augment_directory(self, input_dir, output_dir, ...) -> List[Path]
```

**Key observations:**

- `augment_batch` takes a flat list of images and returns one augmented copy per input (1:1 mapping).
- Multiprocessing is done via `multiprocessing.Pool.imap` with a top-level picklable helper `_augment_one(args)`.
- No random seed is set anywhere — augmentation results are non-deterministic by design (Augraphy applies transforms with random intensity).
- The existing API must remain fully backward-compatible: `augment_batch(images)` must continue to work with no new required arguments.

**Extension point identified:** Add a new method `augment_multi_template` (separate from `augment_batch`) that takes `sources`, `mode`, and per-mode count parameters. This avoids any signature change to `augment_batch`.

---

### 2. Existing Batch Processing Page (`03_batch_processing.py`) — Full Analysis

Current flow:
1. User uploads N files (images or PDFs); PDFs expand page-by-page.
2. Sidebar: preset selectbox, worker slider, parallel checkbox, "Run Batch Augmentation" button.
3. On run: `BatchAugmenter(augmenter=preset, num_workers=n).augment_batch(images, parallel=parallel)`.
4. Results stored in `state.set_batch_results(results)`.
5. ZIP download + thumbnail grid (up to 8 before/after pairs).

ZIP naming: `{original_stem}.png`. For PDFs: `{stem}_p{page}.png`.

**Key design constraints:**
- `st.download_button` is not accessible as `at.download_button` in AppTest — existing tests check `at.metric` labels only.
- No `at.file_uploader` — tests inject images via `at.session_state`.
- Session state key `batch_input_labels` is used for per-file display names.

---

### 3. Session State Keys (Existing)

```python
KEY_BATCH_INPUTS  = "batch_input_images"
KEY_BATCH_RESULTS = "batch_results"
KEY_BATCH_ELAPSED = "batch_elapsed"
```

No `batch_mode`, `batch_copies_per_template`, or `batch_total_outputs` keys exist yet.

---

### 4. Recommended Implementation Approach

#### 4a. New `BatchAugmenter.augment_multi_template` method

```python
def augment_multi_template(
    self,
    sources: List[Image.Image],
    mode: Literal["per_template", "random_sample"],
    copies_per_template: int = 1,   # N×M mode
    total_outputs: int = 10,        # M-total mode
    seed: Optional[int] = None,
    parallel: bool = True,
) -> List[tuple[Image.Image, str]]:
    """Return (augmented_image, source_stem) pairs."""
```

For **N×M mode** (`mode="per_template"`):
- For each source, generate `copies_per_template` augmented copies.
- Total output count = `len(sources) * copies_per_template`.
- ZIP naming: `{source_stem}_{copy_idx:03d}.png`.

For **M-total random mode** (`mode="random_sample"`):
- Use `random.Random(seed).choices(range(len(sources)), k=total_outputs)` to sample indices with replacement.
- Each selected source gets one augmented copy.
- ZIP naming: `{source_stem}_{global_idx:04d}.png` (avoid collisions when the same source is picked multiple times).

Seeding: use `random.Random(seed)` instance (not module-level `random.seed()`) to avoid contaminating the global state. Workers do not need seeding because Augraphy's non-determinism is a feature, not a bug, for data augmentation.

#### 4b. UI changes to `03_batch_processing.py`

Add a mode radio in the sidebar:
```python
batch_mode = st.radio(
    "Augmentation mode",
    ["Single template", "N×M (copies per template)", "M-total (random sample)"],
    key="batch_mode_radio",
)
```

Show conditional inputs:
- N×M mode: `st.number_input("Copies per template", min_value=1, max_value=100, value=3)`
- M-total mode: `st.number_input("Total outputs (M)", min_value=1, max_value=500, value=20)`
- Optional seed: `st.number_input("Random seed (0 = unseeded)", min_value=0, value=0)`

The existing "Single template" mode calls `augment_batch` unchanged. The two new modes call `augment_multi_template`.

ZIP naming in new modes: `{source_stem}_{idx:03d}.png` — driven by `(augmented_image, source_stem)` tuples.

#### 4c. Session state new keys

```python
KEY_BATCH_MODE           = "batch_mode"           # "single" | "per_template" | "random_sample"
KEY_BATCH_COPIES_PER_TPL = "batch_copies_per_tpl" # int
KEY_BATCH_TOTAL_OUTPUTS  = "batch_total_outputs"  # int
KEY_BATCH_SEED           = "batch_seed"           # int | None
```

---

### 5. Gotchas

1. **ZIP naming collisions in M-total mode** — if the same source is picked 5 times, use a global index: `doc_0001.png`, `doc_0002.png`, etc.
2. **Multiprocessing pickling of PIL Images** — `PIL.Image` objects are picklable. Confirmed by existing `augment_batch` implementation.
3. **`random.choices` with seed** — use `random.Random(seed).choices(...)` not `random.seed(); random.choices(...)` to avoid global seed mutation in test environments.
4. **Backward compatibility** — `augment_batch` signature unchanged. All 8 existing `test_batch_processing.py` tests must continue to pass.
5. **AppTest limitation** — tests inject images via `at.session_state` and assert `at.metric` / `at.radio` widgets.
6. **`copies_per_template` validation** — must be >= 1; raise `ValueError` for invalid input.
7. **Large output counts** — display a warning when `total_outputs > 50`.

---

### 6. Dependencies

No new dependencies required. Uses only stdlib `random`, existing `PIL`, `multiprocessing`, and the existing `BatchAugmenter`/`DocumentAugmenter` stack.

---

### Sources

- Existing `src/document_simulator/augmentation/batch.py`
- Existing `src/document_simulator/ui/pages/03_batch_processing.py`
- Existing `tests/test_batch_processing.py` and `tests/ui/integration/test_batch_processing.py`
- `src/document_simulator/ui/state/session_state.py` — session state patterns
- Python `random.Random` docs for seeded instance-level randomness
