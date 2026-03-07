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

---

## 2026-03-07 — Augmentation Lab Catalogue Enhancement

### Context

This section documents research findings for upgrading the Augmentation Lab page
(`src/document_simulator/ui/pages/01_augmentation_lab.py`) from its current design (3 preset
radio buttons + one augmented preview) to a full augmentation catalogue where each Augraphy
transform appears as a thumbnail card, users can toggle transforms on/off, compose a custom
pipeline, and control per-augmentation parameters via sliders that actually drive the output.

---

### 1. Augraphy 8.2.6 — Full Augmentation Catalogue

The installed version (`augraphy==8.2.6`) exports **51 public augmentation classes** from
`augraphy.augmentations`. They are enumerated below, grouped by the natural pipeline phase they
belong to (ink, paper, post), with their key constructor parameters and any known gotchas.

#### 1a. Ink Phase — affects the ink/text layer

| Class | Key constructor params | Notes |
|---|---|---|
| `InkBleed` | `intensity_range`, `kernel_size`, `severity`, `p` | Used in all 3 presets. Reliable. |
| `LowLightNoise` | `num_photons_range`, `alpha_range`, `beta_range`, `gamma_range`, `bias_range`, `dark_current_value`, `exposure_time`, `p` | Replaces deprecated `Fading`. Used in all presets. |
| `BleedThrough` | `intensity_range`, `color_range`, `ksize`, `sigmaX`, `alpha`, `offsets`, `p` | Uses `load_image_from_cache` internally — works standalone but may produce blank bleed-through if no cached image exists; safe to use with `p=1`, the result is just the original when cache is empty. |
| `Letterpress` | `n_samples`, `n_clusters`, `std_range`, `value_range`, `value_threshold_range`, `blur`, `p` | Slow on large images (cluster computation). |
| `LowInkRandomLines` | `count_range`, `use_consistent_lines`, `noise_value`, `p` | Fast. |
| `LowInkPeriodicLines` | `count_range`, `period_range`, `noise_value`, `p` | Fast. |
| `InkColorSwap` | `ink_swap_sequence`, `ink_swap_type`, `ink_swap_iteration`, `ink_swap_color`, `ink_swap_min_width`, `p` | Swaps ink colours — useful for highlighting effects. |
| `InkMottling` | `ink_mottling_alpha_range`, `ink_mottling_noise_scale_range`, `p` | Subtle mottling texture on ink. |
| `InkShifter` | `max_shift_horizontal`, `max_shift_vertical`, `shift_type`, `p` | |
| `Dithering` | `dither`, `order`, `numba_jit`, `p` | Uses Numba JIT — first call is slow (compile); warm up or set `numba_jit=0` for UI previews. |
| `Hollow` | `hollow_median_kernel_value_range`, `hollow_min_width_range`, `p` | |

#### 1b. Paper Phase — affects the underlying paper texture

| Class | Key constructor params | Notes |
|---|---|---|
| `NoiseTexturize` | `sigma_range`, `turbulence_range`, `texture_width_range`, `texture_height_range`, `p` | Used in all presets. Reliable. |
| `ColorShift` | `color_shift_offset_x_range`, `color_shift_offset_y_range`, `color_shift_iterations`, `color_shift_brightness_range`, `color_shift_gaussian_kernel_range`, `p` | Note: NOT a single range — two separate x/y ranges. Used in all presets. |
| `ColorPaper` | `hue_range`, `saturation_range`, `p` | Tints the paper. |
| `Stains` | `stains_type`, `stains_blend_method`, `stains_blend_alpha`, `p` | |
| `WaterMark` | `watermark_word`, `watermark_font_size`, `watermark_font_thickness`, `watermark_font_type`, `watermark_rotation`, `watermark_location`, `watermark_color`, `watermark_method`, `p` | Requires OpenCV `cv2.FONT_*` constants for font type. |
| `BrightnessTexturize` | `range`, `deviation`, `p` | Adds brightness variation across the page. |
| `DelaunayTessellation` | `n_points_range`, `n_horizontal_points_range`, `n_vertical_points_range`, `noise_type`, `color_list`, `color_influence_range`, `p` | Decorative tessellation on paper. |
| `VoronoiTessellation` | `mult_range`, `seed`, `num_cells_range`, `noise_type`, `background_value`, `p` | |
| `PatternGenerator` | `imgx`, `imgy`, `n_rotation_range`, `p` | Alias `quasicrystal.PatternGenerator`. |

#### 1c. Post Phase — affects the printed/scanned document

| Class | Key constructor params | Notes |
|---|---|---|
| `Brightness` | `brightness_range`, `min_brightness`, `min_brightness_value`, `numba_jit`, `p` | Uses Numba JIT — same warm-up caveat as Dithering. |
| `Gamma` | `gamma_range`, `p` | Fast, reliable. |
| `Jpeg` | `quality_range`, `p` | Fast, reliable. |
| `Markup` | `num_lines_range`, `markup_length_range`, `markup_thickness_range`, `markup_type`, `markup_ink`, `markup_color`, `large_word_mode`, `single_word_mode`, `repetitions`, `p` | Used in medium/heavy presets. |
| `Faxify` | `scale_range`, `monochrome`, `monochrome_method`, `monochrome_arguments`, `halftone`, `invert`, `half_kernel_size`, `angle`, `sigma`, `numba_jit`, `p` | Numba JIT. |
| `BadPhotoCopy` | `noise_mask`, `noise_type`, `noise_side`, `noise_iteration`, `noise_size`, `noise_value`, `noise_sparsity`, `noise_concentration`, `blur_noise`, `blur_noise_kernel`, `wave_pattern`, `p` | Visually dramatic; medium speed. |
| `Folding` | `fold_x`, `fold_deviation`, `fold_count`, `fold_noise`, `fold_angle_range`, `gradient_width`, `gradient_height`, `backdrop_color`, `p` | Slow on large images (geometric warping). |
| `BookBinding` | `shadow_radius_range`, `curve_range_right`, `curve_range_left`, `curve_ratio_right`, `curve_ratio_left`, `mirror_range`, `binding_align`, `binding_pages`, `curling_direction`, `backdrop_color`, `enable_shadow`, `p` | Slow — heavy geometric warping. |
| `ShadowCast` | `shadow_side`, `shadow_vertices_range`, `shadow_width_range`, `shadow_height_range`, `shadow_color`, `shadow_opacity_range`, `shadow_iterations_range`, `shadow_blur_kernel_range`, `p` | |
| `LightingGradient` | `light_position`, `direction`, `max_brightness`, `min_brightness`, `mode`, `linear_decay_rate`, `transparency`, `numba_jit`, `p` | Numba JIT. |
| `DirtyDrum` | `line_width_range`, `line_concentration`, `direction`, `noise_intensity`, `noise_value`, `ksize`, `sigmaX`, `p` | |
| `DirtyRollers` | `line_width_range`, `scanline_type`, `p` | |
| `DirtyScreen` | `p` | |
| `GlitchEffect` | `glitch_direction`, `glitch_number_range`, `glitch_size_range`, `glitch_offset_range`, `p` | |
| `Moire` | `moire_density`, `moire_blend_method`, `moire_blend_alpha`, `p` | |
| `NoisyLines` | `noisy_lines_direction`, `noisy_lines_location`, `noisy_lines_number_range`, `noisy_lines_color`, `noisy_lines_noise_intensity_range`, `noisy_lines_stroke_width_range`, `p` | |
| `SubtleNoise` | `subtle_range`, `p` | Very fast and safe. |
| `LinesDegradation` | `line_roi`, `line_gradient_range`, `line_gradient_direction`, `line_split_probability`, `p` | |
| `Scribbles` | `scribbles_type`, `scribbles_ink`, `scribbles_location`, `scribbles_size_range`, `scribbles_count_range`, `scribbles_thickness_range`, `scribbles_brightness_change`, `scribbles_skeletonize`, `scribbles_color`, `scribbles_text`, `p` | |
| `BindingsAndFasteners` | `overlay_types`, `foreground`, `effect_type`, `ntimes`, `nscales`, `edge`, `border_width`, `p` | |
| `PageBorder` | `page_border_width_height`, `page_border_color`, `page_border_background_color`, `page_numbers`, `page_rotation_angle_range`, `curve_frequency`, `curve_height`, `curve_length_one_side`, `same_page_border`, `p` | |
| `Geometric` | `scale`, `translation`, `fliplr`, `flipud`, `crop`, `rotate_range`, `padding`, `padding_type`, `padding_value`, `randomize`, `p` | |
| `Rescale` | `target_dpi`, `source_dpi`, `p` | Changes image resolution. |
| `SectionShift` | `section_shift_x_range`, `section_shift_y_range`, `section_count_range`, `p` | |
| `Squish` | `squish_direction`, `squish_location`, `squish_number_range`, `squish_distance_range`, `p` | |
| `DoubleExposure` | `gaussian_kernel_range`, `offset_direction`, `offset_range`, `p` | Creates double-exposure ghosting. Self-contained — uses only the input image. |
| `ReflectedLight` | `reflected_light_smoothness`, `reflected_light_internal_radius_range`, `reflected_light_external_radius_range`, `p` | |
| `DepthSimulatedBlur` | `p` | |
| `LCDScreenPattern` | `p` | |
| `LensFlare` | `p` | |
| `DotMatrix` | `p` | |

#### 1d. Known Gotchas in 8.2.6

- **No `Fading` class** — use `LowLightNoise` instead (see MEMORY.md).
- **Numba JIT classes** (`Brightness`, `Dithering`, `Faxify`, `LightingGradient`) incur a one-time
  compilation penalty on first call (~2–5 s cold start). For catalogue thumbnails, either warm up
  before rendering or set `numba_jit=0` (slightly slower per-image but no cold start).
- **`BleedThrough`** uses `load_image_from_cache` — safe to instantiate standalone; when no cache
  exists the bleed layer is generated from a noise image rather than a real reverse-side scan.
- **`BookBinding` and `Folding`** are geometric-heavy and slow (~0.5–2 s per 1 MP image).
  Mark them as "slow" in the catalogue and skip them in the auto-generated thumbnail grid unless
  explicitly selected.
- **`Stains`** sometimes produces an all-black output on very small test images
  (< 200 × 200 px); safe on typical document images.
- **`WaterMark`** requires `cv2` constants (`cv2.FONT_HERSHEY_SIMPLEX`) as the default value
  for `watermark_font_type` — this imports OpenCV at construction time.
- **`ColorShift`** takes two separate keyword arguments `color_shift_offset_x_range` and
  `color_shift_offset_y_range`, not a single combined range.
- **`Rescale`** changes the output image resolution — the preview thumbnail will be a different
  size from the original; handle by resizing back to a fixed thumbnail size after applying.

---

### 2. Performance Considerations for a Thumbnail Catalogue

Generating 50+ augmented thumbnails from a single uploaded image simultaneously in Streamlit has
significant performance implications. The following analysis covers what is feasible and what
patterns to use.

#### 2a. Per-augmentation timing estimates (1 MP image, CPU, M-series Mac / comparable)

| Speed tier | Augmentations | Typical time |
|---|---|---|
| Fast (< 100 ms) | `SubtleNoise`, `Jpeg`, `Gamma`, `Brightness`*, `NoiseTexturize`, `ColorShift`, `GlitchEffect`, `DirtyScreen`, `Moire`, `LowInkRandomLines`, `LowInkPeriodicLines`, `DoubleExposure`, `Rescale` | 10–80 ms |
| Medium (100–500 ms) | `InkBleed`, `LowLightNoise`, `BleedThrough`, `Markup`, `Scribbles`, `DirtyDrum`, `DirtyRollers`, `ShadowCast`, `BadPhotoCopy`, `ColorPaper`, `WaterMark`, `Stains`, `Geometric`, `LightingGradient`* | 100–400 ms |
| Slow (> 500 ms) | `Folding`, `BookBinding`, `Letterpress`, `Dithering`*, `Faxify`*, `BrightnessTexturize`, `DelaunayTessellation`, `VoronoiTessellation`, `PatternGenerator` | 500 ms – 4 s |

*First call includes Numba JIT compilation; subsequent calls are fast-tier.

**Total naive sequential cost for all 51 augmentations: ~30–90 s** — clearly too slow for a
live Streamlit session with no caching.

#### 2b. Recommended approach: lazy on-select generation

Do NOT generate all thumbnails at page load time. Instead:

1. **Show the catalogue as a grid of cards** with the augmentation name and a description.
   Cards display the *original* image (or a placeholder) by default.
2. **When the user toggles a card on**, generate only that augmentation's thumbnail at that
   moment, cache the result in `st.session_state`, and immediately display it.
3. **On the first image upload**, optionally pre-generate thumbnails for the ~12 fastest
   augmentations (the "fast" tier above, < 100 ms each) in a background pass to make the
   catalogue feel responsive.
4. **On "Generate catalogue" button press**, run all (or user-selected) augmentations — wrap
   in `st.spinner` and show progress with `st.progress`.

#### 2c. `@st.cache_data` for thumbnail memoization

Wrap the per-augmentation function with `@st.cache_data`. Streamlit will hash the input image
(PIL Image hashing works via the `hash_funcs` mechanism or by converting to bytes for the key).

```python
@st.cache_data(show_spinner=False)
def _apply_single_aug(image_bytes: bytes, aug_name: str, **params) -> bytes:
    """Returns augmented image as PNG bytes, keyed by image + aug_name + params."""
    import numpy as np
    from PIL import Image
    import io
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    aug = _CATALOGUE[aug_name]["factory"](**params)
    result = aug(np.array(img))
    out = io.BytesIO()
    Image.fromarray(result).save(out, format="PNG")
    return out.getvalue()
```

Pass the image as `bytes` (not `PIL.Image`) so Streamlit can hash it correctly. Cache is
invalidated automatically when the uploaded image changes (different bytes = different hash).

#### 2d. Thumbnail sizing

Resize the source image to ~256 × 256 px before applying augmentations for the catalogue
preview. This reduces processing time by 8–16× compared to a 1 MP source. Re-run on the full
image only when the user clicks "Build custom pipeline" or "Augment" with their composed set.

```python
def _thumbnail(img: PIL.Image.Image, size: int = 256) -> PIL.Image.Image:
    img.thumbnail((size, size), PIL.Image.LANCZOS)
    return img
```

---

### 3. Enumerating Augraphy Augmentations Programmatically

The canonical source of truth for what is available in the installed version is:

```python
import inspect
import augraphy.augmentations as aa

CATALOGUE_CLASSES = {
    name: getattr(aa, name)
    for name in aa.__all__
    if inspect.isclass(getattr(aa, name))
}
```

`aa.__all__` (confirmed from `__init__.py`) lists 51 names in 8.2.6:

```
BadPhotoCopy, BindingsAndFasteners, BleedThrough, BookBinding, Brightness,
BrightnessTexturize, ColorPaper, ColorShift, DelaunayTessellation, DepthSimulatedBlur,
DirtyDrum, DirtyRollers, DirtyScreen, Dithering, DotMatrix, DoubleExposure, Faxify,
Folding, Gamma, Geometric, GlitchEffect, Hollow, InkBleed, InkColorSwap, InkMottling,
InkShifter, LCDScreenPattern, Jpeg, LensFlare, Letterpress, LightingGradient,
LinesDegradation, LowInkPeriodicLines, LowInkRandomLines, LowLightNoise, Markup, Moire,
NoiseTexturize, NoisyLines, PageBorder, PatternGenerator, ReflectedLight, Rescale,
Scribbles, SectionShift, ShadowCast, Squish, Stains, SubtleNoise, VoronoiTessellation,
WaterMark
```

For the catalogue, build a static metadata dict (not dynamic inspection at runtime in Streamlit)
because importing all 51 classes at page load adds ~0.5–1 s:

```python
# src/document_simulator/augmentation/catalogue.py
CATALOGUE = {
    "InkBleed": {
        "phase": "ink",
        "description": "Ink bleeds outward from text strokes, simulating wet ink.",
        "speed": "medium",
        "params": {
            "intensity_range": ((0.1, 0.9), "tuple[float,float]", "Bleed intensity"),
            "p": (1.0, "float", "Apply probability"),
        },
        "factory": lambda **kw: InkBleed(**kw),
    },
    # ... one entry per augmentation
}
```

This dict is the single source of truth for the catalogue page — no runtime `inspect` calls.

---

### 4. Best Streamlit Layout for an Augmentation Catalogue

#### 4a. Primary recommendation: tabs by phase + 4-column card grid

```
st.tabs(["Ink Phase", "Paper Phase", "Post Phase", "Custom Pipeline"])

Within each tab:
    st.columns(4) grid — each column holds one augmentation card

Each card:
    st.container(border=True)
        st.image(thumbnail, use_container_width=True)
        st.caption(aug_name)
        st.checkbox("Enable", key=f"aug_enabled_{aug_name}")
        with st.expander("Parameters"):
            # per-aug sliders
```

**Why tabs by phase:** Augraphy's three-phase model maps directly to the pipeline execution
order. Keeping them in tabs reduces visual noise (51 cards in one flat grid is overwhelming)
and teaches users the pipeline structure.

**Why 4 columns:** At 256 px thumbnails, 4 columns fits a standard 1280 px wide layout.
`st.columns(4)` distributes cards evenly. For narrow viewports, drop to `st.columns(2)`.

#### 4b. Alternative: single scrollable grid with phase filter

```
# Phase filter chips (st.radio as horizontal buttons)
phase = st.radio("Phase", ["All", "Ink", "Paper", "Post"], horizontal=True)

# Filtered cards in 4-column grid
visible = [a for a in CATALOGUE if phase == "All" or CATALOGUE[a]["phase"] == phase.lower()]
cols = st.columns(4)
for i, aug_name in enumerate(visible):
    with cols[i % 4]:
        _render_card(aug_name)
```

This is simpler to implement and works well for under 20 visible items at a time.

#### 4c. "Custom Pipeline" tab

After the catalogue tabs, a final tab shows:
- The enabled augmentations in order (drag-to-reorder is not natively supported in Streamlit;
  use `st.multiselect` to let users specify order)
- A single "Augment with custom pipeline" button
- The before/after side-by-side result (reuse existing `show_side_by_side`)

#### 4d. What NOT to use

- **`streamlit-image-gallery`**: External component, adds a dependency, limited control over
  card content (no sliders inside cards).
- **`streamlit-drawable-canvas`**: Irrelevant to this feature.
- **One-tab flat grid of 51 cards**: Too visually dense; users cannot orient themselves.

---

### 5. Connecting Per-Augmentation Sliders to the Actual Augmenter

#### 5a. Current problem

The existing 12 sliders in the sidebar expander are *display-only* — they don't feed into
`DocumentAugmenter`. `DocumentAugmenter._create_pipeline(preset)` always calls
`PresetFactory.create(preset)` which ignores slider values entirely.

#### 5b. What needs to change in `DocumentAugmenter`

Add a second constructor path that accepts an explicit list of configured augmentation objects
(bypassing `PresetFactory`):

```python
class DocumentAugmenter:
    def __init__(
        self,
        pipeline: str = "default",
        custom_augmentations: list | None = None,  # NEW
    ):
        if custom_augmentations is not None:
            # Custom mode: user supplies pre-configured aug objects
            self._augraphy_pipeline = AugraphyPipeline(
                ink_phase=[a for a in custom_augmentations if a._phase == "ink"],
                paper_phase=[a for a in custom_augmentations if a._phase == "paper"],
                post_phase=[a for a in custom_augmentations if a._phase == "post"],
            )
        else:
            self._augraphy_pipeline = self._create_pipeline(pipeline)
```

Note: Augraphy augmentation objects do not carry a `_phase` attribute by default. The
catalogue metadata dict (section 3) tracks phase externally — use that at the UI layer to
separate enabled augmentations into the three lists before passing to `AugraphyPipeline`.

#### 5c. What needs to change in `PresetFactory`

No changes needed to `PresetFactory` itself — it remains the quick-start path. The new custom
path bypasses it entirely.

#### 5d. What needs to change in the page

Replace the preset-only flow with a two-mode UI:

```
Mode A (current): Preset radio → DocumentAugmenter(pipeline=preset)
Mode B (new):     Catalogue toggles + sliders → build aug list →
                  AugraphyPipeline(ink_phase=[...], paper_phase=[...], post_phase=[...])
```

Use `st.radio("Mode", ["Preset", "Custom catalogue"])` to switch.

In custom mode, the page collects:
```python
enabled_augs = []
for aug_name, meta in CATALOGUE.items():
    if st.session_state.get(f"aug_enabled_{aug_name}"):
        params = {k: st.session_state[f"aug_{aug_name}_{k}"] for k in meta["params"]}
        enabled_augs.append(meta["factory"](**params))
```

Then runs:
```python
ink   = [a for (a, name) in zip(enabled_augs, enabled_names) if CATALOGUE[name]["phase"] == "ink"]
paper = [a for (a, name) in zip(enabled_augs, enabled_names) if CATALOGUE[name]["phase"] == "paper"]
post  = [a for (a, name) in zip(enabled_augs, enabled_names) if CATALOGUE[name]["phase"] == "post"]
result = AugraphyPipeline(ink_phase=ink, paper_phase=paper, post_phase=post)(np.array(src))
```

#### 5e. Session state keys for the catalogue

Follow the existing codebase convention of prefixing all keys with the page short name:

```python
f"aug_enabled_{aug_name}"          # bool — checkbox
f"aug_param_{aug_name}_{param_key}"  # float/int — slider value
"aug_catalogue_thumbnails"         # dict[str, bytes] — cached PNG bytes per aug
"aug_mode"                         # "preset" | "catalogue"
```

Add typed accessors to `SessionStateManager` for the new keys (following the pattern in
`src/document_simulator/ui/state/session_state.py`).

---

### 6. Known Constraints: AppTest + Session State

#### 6a. AppTest limitations (Streamlit 1.54.0) — unchanged from existing codebase

From `MEMORY.md` and `CLAUDE.md`:
- No `at.plotly_chart`, `at.download_button`, `at.file_uploader`, `at.image` accessors.
- `at.session_state` is `SafeSessionState` — use `"key" in at.session_state` not `.get()`.
- `streamlit-drawable-canvas` is incompatible; do not introduce it.

#### 6b. Testing the catalogue page

For the new catalogue mode, integration tests should:

1. Inject a pre-baked thumbnail image via `at.session_state["last_uploaded_image"] = pil_img`
   (same pattern as existing `test_augmentation_lab.py`).
2. Set the mode: `at.session_state["aug_mode"] = "catalogue"`.
3. Enable a specific augmentation: `at.session_state["aug_enabled_InkBleed"] = True`.
4. Click the "Generate thumbnail" button.
5. Assert `"aug_catalogue_thumbnails" in at.session_state`.

Avoid testing all 51 augmentations in CI — pick 2–3 representative ones from different speed
tiers. Mark slow-tier augmentation tests with `@pytest.mark.slow`.

#### 6c. Numba JIT in tests

`Brightness` and `Dithering` will hit JIT compilation on first call in a fresh test process,
adding ~3–5 s. Either:
- Use `SubtleNoise` and `Jpeg` as the test augmentations (no Numba).
- Or set `numba_jit=0` in `Brightness(numba_jit=0)` in test fixtures.

#### 6d. `@st.cache_data` in AppTest

`@st.cache_data` decorated functions are **not** mocked or bypassed by AppTest. They execute
normally. This is fine for correctness but means thumbnail tests will actually run the
augmentation (slow). Scope test augmentations to fast-tier only.

---

### 7. Recommended Implementation Approach

#### Phase A — New module: `augmentation/catalogue.py`

Create `src/document_simulator/augmentation/catalogue.py` with:
- A static `CATALOGUE` dict (51 entries) mapping augmentation name to phase, description,
  speed tier, default params, and a factory lambda.
- A helper `apply_single(aug_name: str, image: np.ndarray, **params) -> np.ndarray` function
  that instantiates the augmentation with `p=1` (forced apply) and runs it.
- An `AUGMENTATION_PHASES` dict grouping names by phase for the tab layout.

No changes to `DocumentAugmenter` or `PresetFactory` in this phase.

#### Phase B — Update `DocumentAugmenter`

Add `custom_augmentations: list[Augmentation] | None = None` constructor parameter.
When provided, skip `PresetFactory` and build `AugraphyPipeline` directly from the list,
splitting by phase using the `CATALOGUE` metadata.

Keep backward compatibility: `DocumentAugmenter(pipeline="medium")` must continue to work
exactly as before for the 3-preset radio path and all existing tests.

#### Phase C — Revamp `01_augmentation_lab.py`

Structure:

```
Sidebar:
  Mode radio: "Preset" | "Custom catalogue"

  If preset mode:
    [existing preset radio + sliders — unchanged]

  If catalogue mode:
    [nothing — catalogue controls are in main area]

  "Augment" button (both modes)

Main area:
  File uploader (unchanged)
  Sample data (unchanged)

  If preset mode:
    [existing side-by-side display — unchanged]

  If catalogue mode:
    st.tabs(["Ink Phase", "Paper Phase", "Post Phase", "Custom Pipeline"])
      Each phase tab: 4-column card grid
        Each card: thumbnail image + name + checkbox + params expander
      Custom Pipeline tab:
        st.multiselect to order enabled augmentations
        "Augment" button result (before/after)
```

#### Phase D — Tests

New test file: `tests/ui/integration/test_augmentation_lab_catalogue.py`

Test plan:
- Page loads in catalogue mode without error.
- Catalogue tabs are present.
- Enabling an augmentation via session state and clicking "Generate thumbnail" stores result
  in session state.
- Custom pipeline with 2 enabled augmentations runs and stores augmented image.
- "Augment" button in catalogue mode with no image shows warning.

#### Phase E — SessionStateManager updates

Add new typed keys to `SessionStateManager` for:
- `aug_mode: str` (default `"preset"`)
- `aug_catalogue_thumbnails: dict[str, bytes]`
- `aug_enabled_augs: set[str]`

#### Recommended file changes summary

| File | Change |
|---|---|
| `src/document_simulator/augmentation/catalogue.py` | New file — static catalogue metadata |
| `src/document_simulator/augmentation/augmenter.py` | Add `custom_augmentations` param |
| `src/document_simulator/ui/pages/01_augmentation_lab.py` | Add catalogue mode UI |
| `src/document_simulator/ui/state/session_state.py` | Add catalogue state keys |
| `tests/ui/integration/test_augmentation_lab_catalogue.py` | New test file |
| `docs/features/feature_ui_augmentation_lab.md` | Update with new acceptance criteria |

#### Key design principles to maintain

- No business logic in the page — the page calls `catalogue.apply_single()` and
  `AugraphyPipeline`; it does not import raw augmentation classes directly.
- Sliders in an expander per card — keeps the catalogue scannable by default.
- Preset path is untouched — existing tests continue to pass without modification.
- Thumbnail generation is lazy + cached — never block the full page render.
- The `@st.cache_data` thumbnail function takes `bytes` not `PIL.Image` as input to ensure
  correct Streamlit hashing.

---

### Sources

- [List of Augmentations — augraphy 8.2.0 documentation](https://augraphy.readthedocs.io/en/latest/doc/source/list_of_augmentations.html)
- [How Augraphy Works — augraphy 8.2.0 documentation](https://augraphy.readthedocs.io/en/latest/doc/source/how_augraphy_works.html)
- [Augraphy GitHub — sparkfish/augraphy](https://github.com/sparkfish/augraphy)
- [st.cache_data — Streamlit Docs](https://docs.streamlit.io/library/api-reference/performance/st.cache)
- [Caching overview — Streamlit Docs](https://docs.streamlit.io/develop/concepts/architecture/caching)
- [st.columns — Streamlit Docs](https://docs.streamlit.io/develop/api-reference/layout/st.columns)
- [Layouts and Containers — Streamlit Docs](https://docs.streamlit.io/develop/api-reference/layout)
- [streamlit-image-gallery (GitHub)](https://github.com/virtUOS/streamlit-image-gallery)
- [Defining Custom Pipelines in Augraphy — Sparkfish](https://www.sparkfish.com/augraphy-series-custom-pipelines/)