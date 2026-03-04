# Feature: Synthetic Document Generator

> **GitHub Issue:** `#19`
> **Status:** `planned`
> **Module:** `document_simulator.synthesis` *(to be created)*

---

## Summary

A subsystem for generating synthetic filled-document images from scratch or from a template (PDF, scanned image, blank page). The user visually defines "zones" — bounding boxes placed on the template — and configures each zone with a data provider (Faker), font settings, fill-style, and position-jitter parameters. The generator then produces batches of realistically varied filled documents, complete with `GroundTruth` annotations, ready to feed into the augmentation → OCR pipeline.

---

## Motivation

### Problem Statement

The existing pipeline augments *existing* document images but cannot create new ones. To red-team an OCR system against forms it has never seen before — with varied handwriting styles, different software fills, multi-person forms — we need to be able to synthetically manufacture realistic filled documents at scale from just a template.

Real-world variability we need to simulate:

| Source of variation | Example |
|--------------------|---------|
| Software differences | Word 2016 fill vs Adobe Acrobat fill vs browser autofill |
| Human differences | Person A types in caps; person B uses cursive; person C presses Tab and over-runs the field |
| Physical differences | Pen ink colour, ballpoint vs gel, pencil |
| Scanning differences | Field text shifts if form is not aligned perfectly under scanner lid |

Without synthetic generation, the only way to get this variety is to collect and label thousands of real filled forms — expensive, slow, and privacy-sensitive.

### Value Delivered

- Generate unlimited labelled document images with ground-truth text and bounding boxes.
- Model realistic within-field positioning variation (not just pixel jitter on the whole image).
- Support multi-person forms: zones grouped by "respondent" with independent style settings.
- Output is a `DocumentDataset`-compatible directory: each image paired with a `.json` annotation.
- All generated images feed directly into `DocumentAugmenter` for further degradation.
- Zone configurations are serialisable to JSON for reproducible runs and dataset versioning.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| Data engineer | I upload a blank invoice PDF and define 8 zones | I can generate 1,000 synthetic invoices with realistic fills |
| Researcher | I configure two "respondent" zones with different handwriting styles | I can stress-test a dual-signature form with varied inputs |
| Developer | I load a saved zone config JSON | I reproduce the exact same synthetic dataset for an experiment |
| UI user | I drag bounding boxes onto a form preview and click Generate | I get a ZIP of labelled document images without writing code |
| Pipeline user | I point `DocumentDataset` at the output directory | I can immediately train or evaluate on the synthetic data |

---

## Acceptance Criteria

- [ ] AC-1: `SyntheticDocumentGenerator(template, synthesis_config).generate(n=100)` produces 100 image/annotation pairs in a directory.
- [ ] AC-2: Each annotation is a valid `GroundTruth` JSON readable by `GroundTruthLoader`.
- [ ] AC-3: Zone bounding boxes in annotations correspond to where text was rendered.
- [ ] AC-4: Text content for each zone is drawn from the configured Faker provider on the zone's assigned respondent identity.
- [ ] AC-5: Position jitter distributes text within zone bounds with configurable spread.
- [ ] AC-6: At least three fill styles (`typed`, `form-fill`, `handwritten-font`) produce visually distinct results.
- [ ] AC-7: `SynthesisConfig` (respondents + field types + zones) serialises to/from JSON round-trip stable.
- [ ] AC-8: Each respondent has one or more named field types (e.g. "standard text", "signature"). Each field type has its own independent style profile (font, colour, size, fill style).
- [ ] AC-9: Within a single generated document, all zones assigned to the same respondent + field type combination use a consistent style — as if one person wrote all their standard fields with the same pen, and signed with the same signature style.
- [ ] AC-10: The UI supports N respondents (N ≥ 1), each with M field types (M ≥ 1). Adding a second respondent enables a two-person fill simulation; adding a "signature" field type per respondent enables a distinct signature style.
- [ ] AC-11: The Streamlit UI renders the template on a drawable canvas and zones are placed by dragging rectangles.
- [ ] AC-12: Each drawn zone is assigned to a respondent and a field type via two dropdowns; the zone inherits the resolved style automatically.
- [ ] AC-13: A "Preview (3 samples)" button generates samples in-memory and displays them as a gallery without writing to disk.
- [ ] AC-14: A "Show zone overlays" checkbox draws zone bounding boxes colour-coded by respondent with field-type labels.
- [ ] AC-15: Each preview sample has a re-roll button that regenerates that single sample with a new seed.
- [ ] AC-16: Generated output directories are compatible with `DocumentDataset` without pre-processing.

---

## Proposed Design

### Architecture

```
SynthesisConfig (Pydantic)
    │
    ├─► Template                  — base document: blank | PDF page | image
    ├─► List[RespondentConfig]    — one entry per person filling the form
    │       └─► List[FieldTypeConfig]  — one style profile per field kind for that person
    ├─► List[ZoneConfig]          — what goes where; each zone references respondent_id + field_type_id
    └─► GeneratorConfig           — batch size, seed, output dir

SyntheticDocumentGenerator
    │
    ├─► TemplateLoader.load(source) → PIL Image
    │
    ├─► StyleResolver.resolve(respondent_id, field_type_id, seed)
    │       └─► looks up RespondentConfig → FieldTypeConfig
    │           samples font size once per (respondent, field_type) per document
    │           returns ResolvedStyle(font, size, color, fill_style, jitter_x, jitter_y, ...)
    │
    ├─► ZoneDataSampler(zone, respondent_identity) → str (via seeded Faker)
    │
    ├─► ZoneRenderer.render(canvas, zone, text, resolved_style)
    │       ├─► font family + sampled size + ink colour from ResolvedStyle
    │       ├─► apply position jitter within zone bounds
    │       ├─► apply fill style transform (baseline wander, character spacing)
    │       └─► draw text onto canvas
    │
    ├─► AnnotationBuilder.build(zones, rendered_positions) → GroundTruth
    │
    └─► BatchGenerator.generate(n) → List[(PIL Image, GroundTruth)]
            │
            └─► writes image + JSON to output_dir/
```

### Configuration Models

The hierarchy is: **`SynthesisConfig` → `RespondentConfig` → `FieldTypeConfig` ← `ZoneConfig`**

A respondent owns their identity (who) and a set of field type profiles (what kinds of fields they fill). Zones are purely positional — they reference a respondent and a field type to look up their complete style.

```python
class FieldTypeConfig(BaseModel):
    """
    One style profile for one kind of field that a respondent fills in.
    e.g. a person might have "standard" (typed, black) and "signature" (handwriting, bold, dark blue).
    """
    field_type_id: str              # "standard" | "signature" | "initials" | "date" | ...
    display_name: str               # "Standard text", "Signature", shown in UI

    # Typography
    font_family: str = "sans-serif" # serif | sans-serif | monospace | handwriting
    font_size_range: tuple = (10, 14)  # sampled once per (respondent, field_type) per document
    font_color: str = "#000000"     # ink colour for this field type
    bold: bool = False
    italic: bool = False

    # Fill style
    fill_style: str = "typed"       # typed | form-fill | handwritten-font | stamp

    # Position variation
    jitter_x: float = 0.0
    jitter_y: float = 0.0
    baseline_wander: float = 0.0   # > 0 for handwriting feel
    char_spacing_jitter: float = 0.0


class RespondentConfig(BaseModel):
    """
    One person filling in the form. Owns a list of field type profiles.
    The respondent provides identity (for correlated Faker data) and
    groups field types under one named person.
    """
    respondent_id: str              # "person_a" — foreign key used in ZoneConfig
    display_name: str               # "Person A", shown in UI and zone overlay labels
    field_types: list[FieldTypeConfig]  # at least one; first entry is the default


class ZoneConfig(BaseModel):
    """
    Lightweight — specifies what data goes where and which (respondent, field_type) fills it.
    All style is resolved from FieldTypeConfig; nothing is duplicated here.
    """
    zone_id: str
    label: str                      # field name, e.g. "first_name", "signature", "date_signed"
    box: list[list[float]]          # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] in document pixels
    respondent_id: str = "default"  # → RespondentConfig.respondent_id
    field_type_id: str = "standard" # → FieldTypeConfig.field_type_id within that respondent

    # Data generation
    faker_provider: str             # "name" | "address" | "date" | "ssn" | "bothify:??####"
    custom_values: list[str] = []   # explicit pool — overrides faker if non-empty
    alignment: str = "left"         # left | center | right
```

**Style resolution at generation time:**

```
StyleResolver.resolve(zone.respondent_id, zone.field_type_id)
    → respondent = config.get_respondent(zone.respondent_id)
    → field_type = respondent.get_field_type(zone.field_type_id)
    → ResolvedStyle(
          font    = FontResolver.resolve(field_type.font_family),
          size    = rng.randint(*field_type.font_size_range),   # sampled once, cached per (respondent, field_type, doc)
          color   = field_type.font_color,
          fill    = field_type.fill_style,
          jitter  = (field_type.jitter_x, field_type.jitter_y),
          ...
      )
```

**What stays consistent within one document:** Every zone of "Person A / signature" uses the same sampled font size, the same colour, and the same fill style — as if that person signed all their fields in the same sitting. "Person A / standard text" uses a completely separate style (could be a different colour, different font, different fill).

**What varies across documents:** Font size is re-sampled from the range each time; Faker data is different each time. So each generated document looks like a distinct instance while staying true to each person's style profile.

### Fill Style Taxonomy

| Style | Description | Typical settings |
|-------|-------------|-----------------|
| `form-fill` | Software fills PDF AcroForm fields exactly | Helvetica/Arial, zero jitter, perfect alignment, small font |
| `typed` | User manually typed into a field with a word processor | Monospace or sans-serif, tiny jitter, consistent spacing |
| `handwritten-font` | A handwriting-style font, variable baseline | Cursive/handwriting font, moderate jitter, baseline_wander > 0 |
| `stamp` | Pre-inked rubber stamp or label printer | All-caps, bold, slight rotation, colour shift |
| *(future)* `ballpoint-pen` | Rasterised stroke simulation | Requires ML or vector stroke generation |

### Data Flow: Single Document Generation

```
generate_one(seed)
    │
    ├─► canvas = TemplateLoader.load(template).copy()
    │
    ├─► style_cache = {}   # keyed by (respondent_id, field_type_id)
    │
    ├─► respondent_identities = {
    │       r.respondent_id: generate_respondent(r.respondent_id, seed)
    │       for r in config.respondents
    │   }   # one Faker identity per respondent — correlated fields (name + initials)
    │
    ├─► for each zone in zone_configs:
    │       key     = (zone.respondent_id, zone.field_type_id)
    │       style   = style_cache.setdefault(key, StyleResolver.resolve(key, seed))
    │       text    = ZoneDataSampler.sample(zone, respondent_identities[zone.respondent_id])
    │       pos     = ZoneJitter.apply(zone.box, style.jitter_x, style.jitter_y)
    │       canvas  = ZoneRenderer.draw(canvas, text, style, pos)
    │       regions.append(TextRegion(box=pos, text=text, respondent=zone.respondent_id,
    │                                 field_type=zone.field_type_id))
    │
    ├─► annotation = GroundTruth(image_path=..., text="\n".join(texts), regions=regions)
    │
    └─► return canvas, annotation
```

`style_cache` ensures the font size for "Person A / signature" is sampled exactly once and reused across all signature zones for that person in this document.

### Template Sources

| Source type | Approach |
|------------|----------|
| Blank page | `PIL.Image.new("RGB", (W, H), "white")` |
| Image file | `ImageHandler.load(path)` |
| PDF page | `fitz.open(path)[page_num].get_pixmap(dpi=150)` → PIL Image via PyMuPDF |
| PDF with AcroForm fields | `page.widgets()` → field rects for suggested zone auto-placement |

### UI Design — Zone Editor

The Streamlit page (`00_synthetic_generator.py`) follows a two-panel layout:

**Panel 1 — Template & Zone Drawing**

1. User uploads a PDF or image (or selects "blank page" with width/height inputs).
2. Template is rendered to a PIL Image via `TemplateLoader` and displayed as the background of an `st_canvas` drawable canvas.
3. User selects `drawing_mode="rect"` and drags rectangles directly onto the rendered document. Each drawn rectangle becomes a zone.
4. Coordinates from `result.json_data["objects"]` are scaled from display pixels to document pixels: `doc_px = drawn_px × (render_dpi / display_dpi)`.

**Panel 2 — Respondents & Field Types**

Before configuring zones, the user defines who is filling in the document and what kinds of fields each person fills. Each respondent card contains one or more field type sub-cards.

```
[ + Add respondent ]

▼ Person A                                  ▼ Person B
  Name: [ Person A            ]               Name: [ Person B            ]
  [ + Add field type ]                        [ + Add field type ]

  ▼ Standard text               ▼ Signature    ▼ Standard text
    Ink: [████] #0000CC           Ink: [████] #00008B    Ink: [████] #000000
    Font: Handwriting ▾           Font: Handwriting ▾    Font: Sans-serif ▾
    Size: 10 ──●── 14             Size: 16 ──●── 22      Size: 10 ──●── 12
    Fill: ● handwritten-font      Fill: ● handwritten-font  Fill: ● typed
    Bold: ☐  Italic: ☐            Bold: ☑  Italic: ☑    Bold: ☐  Italic: ☐
    Jitter X/Y: 0.10 / 0.05      Jitter X/Y: 0.05/0.02  Jitter X/Y: 0.03/0.01
    [ 🗑 Remove ]                 [ 🗑 Remove ]           [ 🗑 Remove ]
  [ 🗑 Remove respondent ]                              [ 🗑 Remove respondent ]
```

Each **respondent card** (`st.expander`) contains:

| Control | Widget | Field |
|---------|--------|-------|
| Display name | `st.text_input` | `RespondentConfig.display_name` |
| Add field type button | `st.button("+ Add field type")` | appends to `field_types` list |

Each **field type sub-card** (nested `st.expander`) within a respondent contains:

| Control | Widget | Field |
|---------|--------|-------|
| Field type name | `st.text_input` (e.g. "Signature", "Standard text") | `FieldTypeConfig.display_name` |
| **Ink colour** | `st.color_picker(label="Ink colour")` + preset buttons | `FieldTypeConfig.font_color` |
| Font family | `st.selectbox` (sans-serif, serif, monospace, handwriting) | `FieldTypeConfig.font_family` |
| Font size range | `st.slider(min=6, max=72, value=(10,14))` | `FieldTypeConfig.font_size_range` |
| Fill style | `st.radio` (typed, form-fill, handwritten-font, stamp) | `FieldTypeConfig.fill_style` |
| Bold / Italic | `st.checkbox` | `FieldTypeConfig.bold`, `italic` |
| Position jitter | `st.slider` (0.0–0.5) for X and Y | `FieldTypeConfig.jitter_x/y` |

**Ink colour presets** (quick-select buttons above each field type's colour picker):

| Label | Hex | Simulates |
|-------|-----|-----------|
| Black | `#000000` | Printed / laser |
| Blue ink | `#0000CC` | Ballpoint pen |
| Dark blue | `#00008B` | Fountain pen |
| Red stamp | `#CC0000` | Rubber stamp |
| Pencil grey | `#888888` | Pencil fill |

**Panel 3 — Zone Configuration**

For each drawn zone, a collapsible `st.expander(f"Zone {i}: {label}")` shows only zone-specific fields. All style comes from the resolved `(respondent, field_type)` — nothing is duplicated at the zone level.

| Control | Widget | Field |
|---------|--------|-------|
| Zone label | `st.text_input` | `ZoneConfig.label` |
| **Respondent** | `st.selectbox` of respondent display names | `ZoneConfig.respondent_id` |
| **Field type** | `st.selectbox` filtered to that respondent's field types | `ZoneConfig.field_type_id` |
| Faker provider | `st.selectbox` (name, address, date, ssn, phone, currency, custom…) | `ZoneConfig.faker_provider` |
| Custom value pool | `st.text_area` (one value per line) | `ZoneConfig.custom_values` |
| Alignment | `st.radio` (left, center, right) | `ZoneConfig.alignment` |

The zone expander header shows a colour swatch matching the assigned field type's ink colour and a label like `"Person A / Signature"` so the user can see at a glance exactly which style profile applies.

**Actions bar**

- `st.button("Save config")` → serialises full `SynthesisConfig` (respondents + zones) to JSON download
- `st.file_uploader("Load config")` → restores a previously saved `SynthesisConfig`

**Preview Panel**

A dedicated preview section sits below the zone editor. It is intentionally separate from the full batch generation action so the user can quickly sanity-check zone placement, colour, and data variation before committing to a large batch run.

```
[ 🔍 Preview (3 samples) ]   [ □ Show zone overlays ]

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│              │  │              │  │              │
│   Sample 1   │  │   Sample 2   │  │   Sample 3   │
│   seed=42    │  │   seed=43    │  │   seed=44    │
│              │  │              │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
  [↻ Re-roll]       [↻ Re-roll]       [↻ Re-roll]
```

Implementation:

1. `st.button("Preview (3 samples)")` calls `SyntheticDocumentGenerator.generate_one(seed)` for 3 consecutive seeds — **in-memory only**, no disk write, no ZIP.
2. Results stored as `st.session_state["preview_samples"] = List[(PIL Image, GroundTruth)]`.
3. Gallery rendered with `st.columns(n_preview)` — one column per sample. Each column shows:
   - `st.image(pil_image, caption=f"seed={seed}", use_container_width=True)`
   - A small `st.button("↻", key=f"reroll_{i}")` that regenerates only that slot with `seed + 1000 + i` and updates `preview_samples[i]`.
4. `st.checkbox("Show zone overlays")` — when checked, `overlay_bboxes()` (from the existing `image_display` component) draws each zone rectangle, its label, and a colour-coded border matching the assigned respondent's ink colour. This lets the user verify text placement and see at a glance which zones belong to which person.
5. Preview images are **not** written to the output directory — they are ephemeral session state. Clicking the full "Generate N documents" button runs the proper batch with `output_dir` configured.

**Batch Generation (separate from preview)**

- `st.number_input("Number of documents", min_value=1, value=100)`
- `st.text_input("Output directory")`
- `st.button("Generate batch")` → triggers full `SyntheticDocumentGenerator.generate(n)` with disk write
- After completion: `st.success(f"Generated {n} documents → {output_dir}")` + `st.download_button("Download ZIP")` for in-memory ZIP of all PNG + JSON pairs

### Output Directory Layout

```
output/
├── doc_000001.png          ← rendered image
├── doc_000001.json         ← GroundTruth annotation
├── doc_000002.png
├── doc_000002.json
└── ...
└── synthesis_config.json   ← full SynthesisConfig (respondents + zones + generator settings)
```

This is directly compatible with `DocumentDataset(output_dir)`.

---

## Design Decisions

All design questions were resolved via research. Decisions are final and ready for implementation.

### Q1 — PDF Handling ✅ Resolved

**Decision: `PyMuPDF` (`fitz`) as primary; `pypdfium2` + `pypdf` as fallback if AGPL is a blocker.**

PyMuPDF covers all three requirements from a single pip-installable package (no system dependencies):
- `page.get_pixmap(dpi=150)` → PIL Image at configurable DPI.
- `page.widgets()` → AcroForm field bounding boxes for zone suggestion.
- `page.insert_text()` / widget value setting → optional write-back to filled PDF.

**Licence:** PyMuPDF is AGPL-3.0. AGPL is only triggered when you *distribute* the binary to external users. For an internal non-distributed tool this is not a concern. If this package is ever published to PyPI or shipped to clients, switch to `pypdfium2` (Apache/BSD) + `pypdf` for field introspection.

**Why not `pdf2image`:** Requires `poppler-utils` as a system package — a real burden in Docker and CI. No AcroForm introspection.

### Q2 — Font Resolution & Rendering ✅ Resolved

**Decision: Bundle OFL-licensed TTF files under `src/document_simulator/fonts/` + `PIL.ImageFont.truetype()`.**

`FontResolver` uses a static catalog mapping category names to bundled font paths:

| Category | Font | Licence |
|----------|------|---------|
| `handwriting` | Caveat-Regular.ttf | SIL OFL |
| `handwriting-alt` | Indie Flower | SIL OFL |
| `monospace` | Source Code Pro | SIL OFL |
| `serif` | Merriweather | SIL OFL |
| `sans-serif` | Noto Sans | SIL OFL |

PIL's `ImageDraw.textbbox()` (Pillow ≥ 8.0) is used to measure text before drawing for correct Unicode handling. `reportlab` and `fpdf2` are not used — they are PDF-generation libraries that add unnecessary abstraction when compositing onto a PIL canvas.

**Include fonts in wheel** via `pyproject.toml` `include` / `package_data` so no network or system font access is needed at runtime.

### Q3 — Faker Integration ✅ Resolved

**Decision: `faker` core only. `faker_file` adds nothing for this use case.**

Useful providers for document fields:

| Field | Faker call |
|-------|-----------|
| Full name | `fake.name()` |
| First / last name | `fake.first_name()`, `fake.last_name()` |
| Address | `fake.address()` |
| Date | `fake.date(pattern="%m/%d/%Y")` |
| SSN-like | `fake.ssn()` (en_US) or `fake.numerify("###-##-####")` |
| Phone | `fake.phone_number()` |
| Currency | `fake.pricetag()` or custom format with `fake.pydecimal()` |
| Signature initials | Derived: `f"{first[0]}.{last[0]}."` — not a provider |

`faker_file` generates file *objects* (PDFs, images) for testing file upload/download — entirely unrelated to text-field rendering on a canvas.

### Q4 — Streamlit Zone Editor ✅ Resolved

**Decision: Streamlit + `streamlit-drawable-canvas` for MVP.**

The user draws rectangles directly on the rendered PDF/image. `st_canvas(background_image=pil_image, drawing_mode="rect")` displays the template and returns drawn rectangle coordinates. Each rectangle → `ZoneConfig`. Per-zone configuration (including font colour via `st.color_picker`) appears in expanders alongside the canvas. See **UI Design — Zone Editor** section above for the full widget layout.

**Key implementation notes:**
- Pin `streamlit-drawable-canvas` to a specific version in `pyproject.toml` — maintenance is intermittent.
- Scale drawn coordinates from display pixels to document pixels: `doc_px = drawn_px × (render_dpi / display_dpi)`.
- Add a numeric-input fallback (x1, y1, x2, y2 number inputs) for accessibility and when the canvas fails to load.

### Q5 — Handwriting Simulation ✅ Resolved

**Decision: Handwriting font + Augraphy degradation is sufficient for prototype. Stroke simulation deferred.**

A handwriting font alone is not enough — perfectly consistent letterforms will not stress-test a well-trained OCR model. The Augraphy pipeline (already a dependency) compensates:

1. Render zone text with Caveat or Indie Flower font.
2. Apply Augraphy transforms to the rendered region: `InkBleed` (pen pressure), `LowLightNoise`, slight `Geometric` transform (baseline wobble).
3. Apply per-character position jitter (Q6) to break the uniform font baseline.

**Decision gate:** Measure OCR CER on font-rendered vs real handwritten samples. If gap exceeds ~20 CER points, invest in stroke-level simulation (`hwgen` or IAM dataset compositing). At prototype stage this measurement has not been taken — defer stroke simulation to Future Work.

### Q6 — Jitter Model ✅ Resolved

**Decision: Truncated Gaussian with mean near left edge, σ ≈ 10–15% of zone dimension, plus 3–5% probability of unclamped overflow.**

| Model | Verdict |
|-------|---------|
| Uniform | Too artificial — real writers do not spread uniformly |
| Gaussian | Right shape but allows text to overflow zone — unrealistic |
| Truncated Gaussian | Best fit for real-world form-filling behaviour |

Implementation pattern (rejection sampling — no scipy required):

```python
def truncated_normal(mean, sigma, low, high, rng):
    while True:
        v = rng.normal(mean, sigma)
        if low <= v <= high:
            return v
```

- **Horizontal mean:** left edge + 10–15% of zone width (writers start from the left, not the centre).
- **Vertical jitter:** much smaller than horizontal (σ ≈ 5–8% of zone height).
- **Overflow:** 3–5% probability of drawing from untruncated Gaussian to simulate text running past the field boundary — important for OCR robustness testing.

### Q7 — Existing Tools ✅ Resolved

**Decision: Build from scratch. Borrow compositing idea from SynthDog (MIT); optionally evaluate TRDG for word-image rendering.**

No pip-installable library does zone-aware form filling with configurable synthetic data:
- **SynthDog** (Donut repo, MIT): Script collection, not a library. Composites text onto paper-texture backgrounds. Zone-aware filling and Faker integration are absent. Worth reading for background-texture compositing approach.
- **DocSim / DataSynth**: Research scripts, not installable libraries. Ecosystem too fragmented to depend on.
- **TRDG** (`pip install trdg`, MIT): Generates word/line images for text recognition training. Handles fonts, backgrounds, distortions. Potentially useful for individual zone rendering — evaluate at implementation time.
- **docTR** (Mindee, Apache 2): OCR library, not a generator. Not relevant.

### Q8 — Correlated Fields (Multi-Person Forms) ✅ Resolved

**Decision: One seeded `Faker` instance per respondent per generation call (for data identity); one `StyleResolver` cache entry per `(respondent_id, field_type_id)` per document (for style consistency).**

Data and style are resolved separately:
- **Data identity** (`generate_respondent`): One seeded Faker instance per respondent → correlated fields (name + initials + address all from the same Faker identity).
- **Style** (`StyleResolver` + `style_cache`): Font size is sampled once per `(respondent_id, field_type_id)` pair at the start of `generate_one()` and reused for all zones of that type for that person. This ensures "Person A / signature" zones all render at the same sampled size, while "Person A / standard text" uses its own independently sampled size.

**Factory function for data identity:**

```python
from faker import Faker

def generate_respondent(group_id: str, global_seed: int) -> dict:
    fake = Faker("en_US")
    fake.seed_instance(hash((global_seed, group_id)) & 0xFFFFFFFF)
    first = fake.first_name()
    last  = fake.last_name()
    return {
        "first_name": first,
        "last_name":  last,
        "full_name":  f"{first} {last}",
        "initials":   f"{first[0]}.{last[0]}.",
        "address":    fake.address(),
        "ssn":        fake.ssn(),
    }
```

**Rules for reproducibility:**
- Use `instance.seed_instance()` never `Faker.seed()` (the class method is a global footgun in multi-instance code).
- Call providers in a fixed, explicit sequence — sequence order determines the random state.
- Add new fields only at the *end* of the call sequence to preserve reproducibility for existing fields.
- Pin `faker` version in `pyproject.toml` — internal random sequences can change between Faker releases.
- `Faker` instances are not thread-safe when seeded; create one per respondent per call, not a shared instance.

---

## Proposed Module Structure

```
src/document_simulator/synthesis/
├── __init__.py
├── template.py          # TemplateLoader — blank/image/PDF → PIL Image
├── zones.py             # ZoneConfig (Pydantic), ZoneCollection
├── sampler.py           # ZoneDataSampler — Faker-based text generation per zone
├── renderer.py          # ZoneRenderer — PIL text drawing, jitter, fill styles
├── fonts.py             # FontResolver — category → TTF path, bundled fonts
├── generator.py         # SyntheticDocumentGenerator — orchestrates one/batch generation
└── annotation.py        # AnnotationBuilder → GroundTruth + JSON output
```

And a new UI page:

```
src/document_simulator/ui/pages/
└── 00_synthetic_generator.py   # Zone editor + batch generation UI
```

---

## Package Decisions

| Package | Decision | Notes |
|---------|----------|-------|
| `faker` | **Use** | Core only — covers all required document field providers |
| `faker_file` | **Exclude** | Generates file objects, not text for canvas rendering — no value here |
| `Pillow` | **Use** | Already a dependency; `ImageDraw.text()` + `ImageFont.truetype()` for rendering |
| `PyMuPDF` (fitz) | **Use (primary)** | pip-installable, no system deps, covers render + AcroForm + write-back; AGPL OK for internal tool |
| `pypdfium2` + `pypdf` | **Use (AGPL fallback)** | If tool is ever distributed externally, replace PyMuPDF with this pair |
| `pdf2image` | **Exclude** | Requires poppler system package; no AcroForm support |
| `fpdf2` / `reportlab` | **Defer** | Only needed if export-to-filled-PDF feature is added (Future Work) |
| `streamlit-drawable-canvas` | **Use (pinned)** | Only viable drag-to-draw option; pin version; add numeric-input fallback |
| Google Fonts TTFs (OFL) | **Bundle** | Caveat, Source Code Pro, Merriweather, Noto Sans — all SIL OFL licensed |

---

## Integration with Existing Pipeline

```
Synthetic Document Generator
    │
    output/doc_NNNNNN.png + .json
    │
    ▼
DocumentDataset(output_dir)          ← existing feature #8
    │
    ▼
DocumentAugmenter("heavy")           ← existing feature #2
    │
    ▼
OCREngine.recognize()                ← existing feature #4
    │
    ▼
Evaluator.evaluate_dataset()         ← existing feature #11
    │
    ▼
RLTrainer (PPO agent)                ← existing feature #10
```

The generator becomes the *source of truth* for document data, replacing the need for a real scanned document corpus.

---

## Research Status

All design questions (Q1–Q8) have been researched and resolved. See **Design Decisions** section above. The feature is ready for TDD implementation.

---

## Future Work

- [ ] Stroke-based handwriting simulation (pen pressure, speed modelling).
- [ ] Checkbox / radio button zone types.
- [ ] Signature zone: loop-based glyph generation.
- [ ] Multi-page PDF template support.
- [ ] AcroForm auto-detection to suggest zone placement from an existing PDF form.
- [ ] Export filled PDF (not just PNG) for downstream PDF-native extraction testing.

---

## References

- [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md)
- [RESEARCH_FINDINGS.md](../RESEARCH_FINDINGS.md)
- [feature_document_augmenter.md](feature_document_augmenter.md)
- [feature_document_dataset.md](feature_document_dataset.md)
- [feature_ground_truth.md](feature_ground_truth.md)
- [SynthDog — CLOVA AI](https://github.com/clovaai/donut)
- [Faker documentation](https://faker.readthedocs.io/)
