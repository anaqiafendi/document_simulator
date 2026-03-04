# UI_PLAN.md — Streamlit Interface for Document Simulator

## 1. Overview

### Goals

Build a Streamlit web UI that wraps every function of the `document_simulator` package so a user
can upload images, run augmentation, perform OCR, evaluate pipelines, and launch RL training —
all from a browser, with zero CLI knowledge required.

### Design Principles

- **One page per subsystem** — Augmentation, OCR, Batch, Evaluation, RL Training
- **Show the data** — always display raw outputs (images, text, bounding boxes, reward curves)
- **TDD throughout** — every component and page has failing tests written first
- **No business logic in pages** — pages call package functions; all logic lives in
  `document_simulator.*` or thin `ui/components/` helpers

### How to Run (after implementation)

```bash
# Install UI deps
uv sync --extra ui

# Launch
uv run streamlit run src/document_simulator/ui/app.py

# Run UI tests only
uv run pytest tests/ui/ -q
```

---

## 2. Architecture

### File Structure

```
src/document_simulator/
└── ui/
    ├── __init__.py
    ├── app.py                        # Home page + navigation
    ├── pages/
    │   ├── 01_augmentation_lab.py    # Augmentation Lab
    │   ├── 02_ocr_engine.py          # OCR Engine
    │   ├── 03_batch_processing.py    # Batch Processing
    │   ├── 04_evaluation.py          # Evaluation Dashboard
    │   └── 05_rl_training.py         # RL Training
    ├── components/
    │   ├── __init__.py
    │   ├── image_display.py          # Side-by-side images, bbox overlay
    │   ├── metrics_charts.py         # Plotly bar/line/box charts
    │   ├── file_uploader.py          # Shared upload widget + validation
    │   └── progress_tracker.py       # Training step counter + reward plot
    └── state/
        ├── __init__.py
        └── session_state.py          # Typed SessionState wrapper

tests/
└── ui/
    ├── conftest.py                   # Shared fixtures (fake images, mock engines)
    ├── unit/
    │   ├── test_image_display.py
    │   ├── test_metrics_charts.py
    │   ├── test_file_uploader.py
    │   └── test_session_state.py
    ├── integration/
    │   ├── test_augmentation_lab.py
    │   ├── test_ocr_engine_page.py
    │   ├── test_batch_processing.py
    │   ├── test_evaluation.py
    │   └── test_rl_training.py
    └── e2e/
        └── test_full_flow.py
```

### Dependency Graph

```
app.py
 ├── pages/01_augmentation_lab.py
 │     ├── components/image_display.py
 │     ├── components/file_uploader.py
 │     └── state/session_state.py
 │           └── document_simulator.augmentation.*
 ├── pages/02_ocr_engine.py
 │     ├── components/image_display.py   (bbox overlay)
 │     ├── components/metrics_charts.py  (confidence bar)
 │     └── state/session_state.py
 │           └── document_simulator.ocr.*
 ├── pages/03_batch_processing.py
 │     ├── components/file_uploader.py   (multi-file)
 │     ├── components/progress_tracker.py
 │     └── state/session_state.py
 │           └── document_simulator.augmentation.batch
 ├── pages/04_evaluation.py
 │     ├── components/metrics_charts.py
 │     └── state/session_state.py
 │           └── document_simulator.evaluation.*
 └── pages/05_rl_training.py
       ├── components/progress_tracker.py
       ├── components/metrics_charts.py
       └── state/session_state.py
             └── document_simulator.rl.*
```

---

## 3. Page Wireframes

### Home (app.py)

```
┌─────────────────────────────────────────────────────────────────┐
│  Document Simulator                                              │
│  ─────────────────────────────────────────────────────────────  │
│  Document image augmentation + OCR + RL Optimisation            │
│                                                                   │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │ Aug Lab   │  │ OCR       │  │ Batch     │  │ Evaluate  │    │
│  │  →        │  │  →        │  │  →        │  │  →        │    │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │
│  ┌───────────┐                                                    │
│  │ RL Train  │                                                    │
│  │  →        │                                                    │
│  └───────────┘                                                    │
│                                                                   │
│  Quick-start: upload an image below and augment in one click     │
│  [ Drop image here / Browse ]                   [Augment →]      │
└─────────────────────────────────────────────────────────────────┘
```

### Page 1 — Augmentation Lab

```
┌─────────────────────────────────────────────────────────────────┐
│  🔬 Augmentation Lab                                             │
│  ─────────────────────────────────────────────────────────────  │
│  ┌── Sidebar ─────────────────┐                                  │
│  │  Pipeline preset           │   ┌── Original ──┐  ┌── Aug ──┐ │
│  │  ○ light  ● medium  ○ heavy│   │              │  │         │ │
│  │                             │   │  [image]     │  │ [image] │ │
│  │  ▼ Advanced parameters      │   │              │  │         │ │
│  │  InkBleed prob   [──●──]   │   └──────────────┘  └─────────┘ │
│  │  InkBleed intens [──●──]   │                                  │
│  │  Fading prob     [──●──]   │   Parameters applied             │
│  │  Noise prob      [──●──]   │   ┌──────────────────────────┐  │
│  │  Noise sigma     [──●──]   │   │  ink_bleed_p:   0.50     │  │
│  │  ColorShift prob [──●──]   │   │  noise_sigma:   8.20     │  │
│  │  Brightness prob [──●──]   │   │  ...                     │  │
│  │  Brightness spread[──●──]  │   └──────────────────────────┘  │
│  │  Gamma prob      [──●──]   │                                  │
│  │  Markup prob     [──●──]   │   [Download augmented image]     │
│  │  Jpeg prob       [──●──]   │                                  │
│  │                             │                                  │
│  │  [Augment Image]            │                                  │
│  └────────────────────────────┘                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Page 2 — OCR Engine

```
┌─────────────────────────────────────────────────────────────────┐
│  🔍 OCR Engine                                                    │
│  ─────────────────────────────────────────────────────────────  │
│  ┌── Sidebar ─────────────────┐                                  │
│  │  Language    [en ▼]        │   ┌── Image + Bounding Boxes ──┐ │
│  │  GPU         [ ] off       │   │  ┌──────┐ ┌────────────┐  │ │
│  │                             │   │  │Hello │ │   World    │  │ │
│  │  Ground Truth (optional)    │   │  └──────┘ └────────────┘  │ │
│  │  [Drop .txt file here]      │   │  [image with overlaid     │ │
│  │                             │   │   green bounding boxes]   │ │
│  │  [Run OCR]                  │   └───────────────────────────┘ │
│  └────────────────────────────┘                                  │
│                                                                   │
│  ┌── Extracted Text ──────────┐   ┌── Metrics ─────────────────┐ │
│  │  Hello World               │   │  Mean confidence:  0.923   │ │
│  │  Invoice #1234             │   │  Regions detected: 12      │ │
│  │  Date: 2024-01-01          │   │  CER (vs GT):      0.041   │ │
│  │                             │   │  WER (vs GT):      0.062   │ │
│  └────────────────────────────┘   └────────────────────────────┘ │
│                                                                   │
│  ┌── Region Table ────────────────────────────────────────────┐  │
│  │  #   Text              Confidence   Box                     │  │
│  │  1   Hello             0.99         [12,5],[82,5],...       │  │
│  │  2   World             0.91         [90,5],[180,5],...      │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Page 3 — Batch Processing

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚙️ Batch Processing                                              │
│  ─────────────────────────────────────────────────────────────  │
│  ┌── Sidebar ─────────────────┐                                  │
│  │  Pipeline  [medium ▼]      │   [Drop images here / Browse]    │
│  │  Workers   [4 ──●──── 8]   │   invoice_001.jpg  ✓            │
│  │  Parallel  [✓]             │   invoice_002.jpg  ✓            │
│  │                             │   form_001.png     ✓            │
│  │  [Run Batch Augmentation]   │                                  │
│  └────────────────────────────┘   Processing...                  │
│                                   ████████░░░░  8/12 images      │
│                                                                   │
│  ┌── Results ─────────────────────────────────────────────────┐  │
│  │  Processed: 12 images   Time: 4.2s   Throughput: 2.9 img/s │  │
│  │  [Download all as ZIP]                                      │  │
│  │                                                              │  │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐        │  │
│  │  │orig  │  │orig  │  │orig  │  │orig  │  │ ...  │        │  │
│  │  │ aug  │  │ aug  │  │ aug  │  │ aug  │  │      │        │  │
│  │  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘        │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Page 4 — Evaluation Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│  📊 Evaluation Dashboard                                          │
│  ─────────────────────────────────────────────────────────────  │
│  ┌── Sidebar ─────────────────┐                                  │
│  │  Dataset dir               │   ┌── CER Comparison ─────────┐ │
│  │  [./data/test ]            │   │  ■ Original   ■ Augmented  │ │
│  │                             │   │    0.04          0.12     │ │
│  │  Pipeline  [medium ▼]      │   │   [bar chart]            │ │
│  │                             │   └───────────────────────────┘ │
│  │  [Run Evaluation]           │                                  │
│  └────────────────────────────┘   ┌── WER Comparison ─────────┐ │
│                                    │    0.06          0.18     │ │
│  ┌── Summary Table ──────────┐    │   [bar chart]            │ │
│  │  Metric      Orig   Aug   │    └───────────────────────────┘ │
│  │  CER mean    0.04   0.12  │                                  │
│  │  CER std     0.01   0.03  │   ┌── Confidence Dist. ───────┐ │
│  │  WER mean    0.06   0.18  │   │   [box plot: orig vs aug] │ │
│  │  WER std     0.02   0.05  │   └───────────────────────────┘ │
│  │  Conf mean   0.94   0.87  │                                  │
│  │  n_samples   200          │   ┌── Sample Grid ─────────────┐ │
│  └───────────────────────────┘   │  orig / aug pairs (6 max)  │ │
│                                    └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Page 5 — RL Training

```
┌─────────────────────────────────────────────────────────────────┐
│  🤖 RL Training                                                   │
│  ─────────────────────────────────────────────────────────────  │
│  ┌── Sidebar ─────────────────┐                                  │
│  │  Dataset dir               │   ┌── Training Progress ───────┐ │
│  │  [./data/train ]           │   │  Step: 24,800 / 100,000    │ │
│  │                             │   │  ████████████░░░░  24.8%  │ │
│  │  Learning rate [3e-4     ] │   └───────────────────────────┘ │
│  │  Batch size    [64       ] │                                  │
│  │  N steps       [2048     ] │   ┌── Reward Curve ────────────┐ │
│  │  Num envs      [4 ─●── 8] │   │   [line chart: step→reward] │ │
│  │  Total steps   [100000   ] │   │    0.6                      │ │
│  │  Checkpoint freq[10000   ] │   │   ╭────────────────         │ │
│  │                             │   │  ╭╯                        │ │
│  │  [▶ Start Training]         │   │ ╭╯                         │ │
│  │  [⏹ Stop]                   │   │╭╯                          │ │
│  │  [💾 Save Model]            │   │0                           │ │
│  │  [📂 Load Model]            │   └───────────────────────────┘ │
│  └────────────────────────────┘                                  │
│                                   ┌── Last Eval ───────────────┐ │
│                                   │  CER:   0.087              │ │
│                                   │  CAR:   0.913              │ │
│                                   │  Conf:  0.891              │ │
│                                   │  SSIM:  0.714              │ │
│                                   └───────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Dependency Changes

### Add `ui` extra to `pyproject.toml`

```toml
[project.optional-dependencies]
ui = [
    "streamlit>=1.32.0",
    "plotly>=5.20.0",
    "pandas>=2.2.0",   # already a core dep — no change needed
]
```

Add to `[tool.uv]` dev-dependencies (for testing):
```toml
# AppTest is bundled in streamlit — no extra test package needed
```

### Install

```bash
uv sync --extra ui --native-tls
```

### Launch script (convenience)

Add to `[project.scripts]` in `pyproject.toml`:
```toml
document-simulator-ui = "document_simulator.ui.app:launch"
```

---

## 5. Session State Design

`state/session_state.py` wraps `st.session_state` with typed accessors so pages never
write raw string keys:

```python
# Key names (never spelled out in page files)
KEY_LAST_UPLOADED_IMAGE  = "last_uploaded_image"    # PIL.Image | None
KEY_LAST_AUG_IMAGE       = "last_aug_image"          # PIL.Image | None
KEY_LAST_OCR_RESULT      = "last_ocr_result"         # dict | None
KEY_EVAL_RESULTS         = "eval_results"            # dict | None
KEY_TRAINING_LOG         = "training_log"            # list[dict] | None
KEY_TRAINING_RUNNING     = "training_running"        # bool
KEY_RL_MODEL_PATH        = "rl_model_path"           # Path | None
```

---

## 6. TDD Implementation Phases

Each phase follows strict Red → Green → Refactor:
1. **Red** — write a failing test (uses `streamlit.testing.v1.AppTest` or plain pytest)
2. **Green** — write the minimum code to pass
3. **Refactor** — clean up without breaking tests

---

### Phase 1 — Foundation

**Scope**: Package scaffold, `pyproject.toml` update, shared `conftest.py`, session state.

#### 1.1 — Dependency & scaffold

**Files to create**:
- `src/document_simulator/ui/__init__.py`
- `src/document_simulator/ui/app.py` (stub)
- `src/document_simulator/ui/state/__init__.py`
- `src/document_simulator/ui/state/session_state.py`
- `src/document_simulator/ui/components/__init__.py`
- `tests/ui/__init__.py`
- `tests/ui/conftest.py`

**Update**: `pyproject.toml` — add `ui` optional dependency group.

##### RED — failing tests

`tests/ui/conftest.py`:
```python
import numpy as np
import pytest
from PIL import Image


@pytest.fixture
def blank_image():
    """224×224 white RGB image."""
    return Image.fromarray(np.full((224, 224, 3), 255, dtype=np.uint8))


@pytest.fixture
def sample_ocr_result():
    return {
        "text": "Hello World",
        "boxes": [[[10, 5], [80, 5], [80, 25], [10, 25]]],
        "scores": [0.95],
        "raw": None,
    }


@pytest.fixture
def sample_eval_metrics():
    return {
        "n_samples": 10,
        "mean_original_cer": 0.04,
        "std_original_cer": 0.01,
        "mean_augmented_cer": 0.12,
        "std_augmented_cer": 0.03,
        "mean_original_wer": 0.06,
        "std_original_wer": 0.01,
        "mean_augmented_wer": 0.18,
        "std_augmented_wer": 0.04,
        "mean_original_confidence": 0.94,
        "std_original_confidence": 0.02,
        "mean_augmented_confidence": 0.87,
        "std_augmented_confidence": 0.04,
    }
```

`tests/ui/unit/test_session_state.py`:
```python
from unittest.mock import patch, MagicMock
import pytest


def test_session_state_imports():
    from document_simulator.ui.state.session_state import SessionStateManager
    assert SessionStateManager is not None


def test_get_uploaded_image_returns_none_when_unset():
    from document_simulator.ui.state.session_state import SessionStateManager
    mock_state = {}
    with patch("streamlit.session_state", mock_state):
        mgr = SessionStateManager()
        assert mgr.get_uploaded_image() is None


def test_set_and_get_uploaded_image(blank_image):
    from document_simulator.ui.state.session_state import SessionStateManager
    mock_state = {}
    with patch("streamlit.session_state", mock_state):
        mgr = SessionStateManager()
        mgr.set_uploaded_image(blank_image)
        assert mgr.get_uploaded_image() is not None


def test_set_and_get_ocr_result(sample_ocr_result):
    from document_simulator.ui.state.session_state import SessionStateManager
    mock_state = {}
    with patch("streamlit.session_state", mock_state):
        mgr = SessionStateManager()
        mgr.set_ocr_result(sample_ocr_result)
        result = mgr.get_ocr_result()
        assert result["text"] == "Hello World"


def test_training_not_running_by_default():
    from document_simulator.ui.state.session_state import SessionStateManager
    mock_state = {}
    with patch("streamlit.session_state", mock_state):
        mgr = SessionStateManager()
        assert mgr.is_training_running() is False


def test_clear_resets_all_keys():
    from document_simulator.ui.state.session_state import SessionStateManager
    mock_state = {"last_uploaded_image": "x", "training_running": True}
    with patch("streamlit.session_state", mock_state):
        mgr = SessionStateManager()
        mgr.clear()
        assert mgr.get_uploaded_image() is None
        assert mgr.is_training_running() is False
```

##### GREEN — implementation

`src/document_simulator/ui/state/session_state.py`:
```python
from typing import Any, Optional
from PIL import Image
import streamlit as st

KEY_LAST_UPLOADED_IMAGE = "last_uploaded_image"
KEY_LAST_AUG_IMAGE = "last_aug_image"
KEY_LAST_OCR_RESULT = "last_ocr_result"
KEY_EVAL_RESULTS = "eval_results"
KEY_TRAINING_LOG = "training_log"
KEY_TRAINING_RUNNING = "training_running"
KEY_RL_MODEL_PATH = "rl_model_path"

_ALL_KEYS = [
    KEY_LAST_UPLOADED_IMAGE, KEY_LAST_AUG_IMAGE, KEY_LAST_OCR_RESULT,
    KEY_EVAL_RESULTS, KEY_TRAINING_LOG, KEY_TRAINING_RUNNING, KEY_RL_MODEL_PATH,
]


class SessionStateManager:
    def get_uploaded_image(self) -> Optional[Image.Image]:
        return st.session_state.get(KEY_LAST_UPLOADED_IMAGE)

    def set_uploaded_image(self, image: Image.Image) -> None:
        st.session_state[KEY_LAST_UPLOADED_IMAGE] = image

    def get_aug_image(self) -> Optional[Image.Image]:
        return st.session_state.get(KEY_LAST_AUG_IMAGE)

    def set_aug_image(self, image: Image.Image) -> None:
        st.session_state[KEY_LAST_AUG_IMAGE] = image

    def get_ocr_result(self) -> Optional[dict]:
        return st.session_state.get(KEY_LAST_OCR_RESULT)

    def set_ocr_result(self, result: dict) -> None:
        st.session_state[KEY_LAST_OCR_RESULT] = result

    def get_eval_results(self) -> Optional[dict]:
        return st.session_state.get(KEY_EVAL_RESULTS)

    def set_eval_results(self, results: dict) -> None:
        st.session_state[KEY_EVAL_RESULTS] = results

    def is_training_running(self) -> bool:
        return st.session_state.get(KEY_TRAINING_RUNNING, False)

    def set_training_running(self, running: bool) -> None:
        st.session_state[KEY_TRAINING_RUNNING] = running

    def get_training_log(self) -> list:
        return st.session_state.get(KEY_TRAINING_LOG, [])

    def append_training_log(self, entry: dict) -> None:
        log = st.session_state.get(KEY_TRAINING_LOG, [])
        log.append(entry)
        st.session_state[KEY_TRAINING_LOG] = log

    def clear(self) -> None:
        for key in _ALL_KEYS:
            st.session_state.pop(key, None)
```

##### REFACTOR
- Add type hints for all return values
- Move key constants to a single `_KEYS` module-level dict for easier iteration

---

#### 1.2 — Image Display Component

**File**: `src/document_simulator/ui/components/image_display.py`

Responsibilities:
- `show_side_by_side(original, augmented)` — renders two `st.image` calls in columns
- `overlay_bboxes(image, boxes, scores)` — draws bounding boxes on a PIL image with
  colour-coded confidence (green = high, red = low) and returns the annotated PIL image

##### RED — failing tests

`tests/ui/unit/test_image_display.py`:
```python
import numpy as np
import pytest
from PIL import Image


@pytest.fixture
def blank_image():
    return Image.fromarray(np.full((100, 100, 3), 255, dtype=np.uint8))


def test_overlay_bboxes_returns_pil_image(blank_image):
    from document_simulator.ui.components.image_display import overlay_bboxes
    boxes = [[[10, 5], [80, 5], [80, 25], [10, 25]]]
    scores = [0.95]
    result = overlay_bboxes(blank_image, boxes, scores)
    assert isinstance(result, Image.Image)


def test_overlay_bboxes_same_size(blank_image):
    from document_simulator.ui.components.image_display import overlay_bboxes
    boxes = [[[10, 5], [80, 5], [80, 25], [10, 25]]]
    result = overlay_bboxes(blank_image, boxes, [0.9])
    assert result.size == blank_image.size


def test_overlay_bboxes_empty_boxes(blank_image):
    from document_simulator.ui.components.image_display import overlay_bboxes
    result = overlay_bboxes(blank_image, [], [])
    assert isinstance(result, Image.Image)


def test_overlay_bboxes_colour_high_confidence(blank_image):
    """High confidence box should draw in green range (R < 100)."""
    from document_simulator.ui.components.image_display import _confidence_colour
    r, g, b = _confidence_colour(0.99)
    assert g > r   # more green than red = good confidence


def test_overlay_bboxes_colour_low_confidence(blank_image):
    """Low confidence box should draw in red range (R > G)."""
    from document_simulator.ui.components.image_display import _confidence_colour
    r, g, b = _confidence_colour(0.10)
    assert r > g


def test_image_to_bytes_returns_bytes(blank_image):
    from document_simulator.ui.components.image_display import image_to_bytes
    result = image_to_bytes(blank_image)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_image_to_bytes_accepts_numpy(blank_image):
    import numpy as np
    from document_simulator.ui.components.image_display import image_to_bytes
    arr = np.array(blank_image)
    result = image_to_bytes(arr)
    assert isinstance(result, bytes)
```

##### GREEN — implementation

`src/document_simulator/ui/components/image_display.py`:
```python
import io
from typing import List, Tuple
import numpy as np
from PIL import Image, ImageDraw
import streamlit as st


def _confidence_colour(score: float) -> Tuple[int, int, int]:
    """Map confidence in [0, 1] to an (R, G, B) colour (red=low, green=high)."""
    r = int((1.0 - score) * 255)
    g = int(score * 255)
    return r, g, 0


def overlay_bboxes(
    image: Image.Image,
    boxes: List,
    scores: List[float],
    line_width: int = 2,
) -> Image.Image:
    """Draw quadrilateral bounding boxes onto a PIL image."""
    out = image.convert("RGB").copy()
    draw = ImageDraw.Draw(out)
    for box, score in zip(boxes, scores):
        colour = _confidence_colour(float(score))
        pts = [(int(p[0]), int(p[1])) for p in box]
        draw.polygon(pts, outline=colour)
    return out


def image_to_bytes(image, fmt: str = "PNG") -> bytes:
    """Encode a PIL Image or numpy array to PNG bytes for st.download_button."""
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image.astype(np.uint8))
    buf = io.BytesIO()
    image.save(buf, format=fmt)
    return buf.getvalue()


def show_side_by_side(
    original: Image.Image,
    augmented: Image.Image,
    labels: Tuple[str, str] = ("Original", "Augmented"),
) -> None:
    """Render two images in equal-width Streamlit columns."""
    col1, col2 = st.columns(2)
    with col1:
        st.image(original, caption=labels[0], use_container_width=True)
    with col2:
        st.image(augmented, caption=labels[1], use_container_width=True)
```

##### REFACTOR
- Extract `_poly_to_points` helper for box format normalisation
- Support both `[[x,y],[x,y],...]` and `[x1,y1,x2,y2,...]` flat formats

---

#### 1.3 — Metrics Charts Component

**File**: `src/document_simulator/ui/components/metrics_charts.py`

Responsibilities:
- `cer_wer_bar(metrics)` → Plotly Figure: grouped bar chart (Original vs Augmented CER/WER)
- `confidence_box(original_scores, augmented_scores)` → Plotly Figure: box plot
- `reward_line(log_entries)` → Plotly Figure: line chart (step vs reward)

##### RED — failing tests

`tests/ui/unit/test_metrics_charts.py`:
```python
import pytest


def test_cer_wer_bar_returns_figure(sample_eval_metrics):
    from document_simulator.ui.components.metrics_charts import cer_wer_bar
    import plotly.graph_objects as go
    fig = cer_wer_bar(sample_eval_metrics)
    assert isinstance(fig, go.Figure)


def test_cer_wer_bar_has_two_traces(sample_eval_metrics):
    from document_simulator.ui.components.metrics_charts import cer_wer_bar
    fig = cer_wer_bar(sample_eval_metrics)
    assert len(fig.data) == 2   # Original and Augmented


def test_reward_line_returns_figure():
    from document_simulator.ui.components.metrics_charts import reward_line
    import plotly.graph_objects as go
    log = [{"step": 0, "reward": 0.1}, {"step": 1000, "reward": 0.4}]
    fig = reward_line(log)
    assert isinstance(fig, go.Figure)


def test_reward_line_empty_log_returns_empty_figure():
    from document_simulator.ui.components.metrics_charts import reward_line
    fig = reward_line([])
    assert len(fig.data) == 0 or fig.data[0].y == ()


def test_confidence_box_returns_figure():
    from document_simulator.ui.components.metrics_charts import confidence_box
    import plotly.graph_objects as go
    fig = confidence_box([0.9, 0.95, 0.88], [0.75, 0.80, 0.70])
    assert isinstance(fig, go.Figure)


def test_confidence_box_has_two_traces():
    from document_simulator.ui.components.metrics_charts import confidence_box
    fig = confidence_box([0.9, 0.95], [0.75, 0.80])
    assert len(fig.data) == 2
```

##### GREEN — implementation

`src/document_simulator/ui/components/metrics_charts.py`:
```python
from typing import Dict, List, Any
import plotly.graph_objects as go


def cer_wer_bar(metrics: Dict[str, Any]) -> go.Figure:
    """Grouped bar chart comparing CER and WER for original vs augmented."""
    categories = ["CER", "WER"]
    orig_vals = [
        metrics.get("mean_original_cer", 0),
        metrics.get("mean_original_wer", 0),
    ]
    aug_vals = [
        metrics.get("mean_augmented_cer", 0),
        metrics.get("mean_augmented_wer", 0),
    ]
    fig = go.Figure(data=[
        go.Bar(name="Original", x=categories, y=orig_vals, marker_color="#2196F3"),
        go.Bar(name="Augmented", x=categories, y=aug_vals, marker_color="#FF9800"),
    ])
    fig.update_layout(barmode="group", title="CER / WER: Original vs Augmented",
                      yaxis_title="Error Rate", yaxis_range=[0, 1])
    return fig


def confidence_box(
    original_scores: List[float],
    augmented_scores: List[float],
) -> go.Figure:
    """Box plot of confidence score distributions."""
    fig = go.Figure(data=[
        go.Box(y=original_scores, name="Original", marker_color="#2196F3"),
        go.Box(y=augmented_scores, name="Augmented", marker_color="#FF9800"),
    ])
    fig.update_layout(title="OCR Confidence Distribution", yaxis_title="Confidence",
                      yaxis_range=[0, 1])
    return fig


def reward_line(log_entries: List[Dict[str, Any]]) -> go.Figure:
    """Line chart of RL reward over training steps."""
    if not log_entries:
        return go.Figure()
    steps = [e["step"] for e in log_entries]
    rewards = [e["reward"] for e in log_entries]
    fig = go.Figure(data=[
        go.Scatter(x=steps, y=rewards, mode="lines+markers",
                   line={"color": "#4CAF50"}, name="Reward"),
    ])
    fig.update_layout(title="Training Reward", xaxis_title="Step",
                      yaxis_title="Reward")
    return fig
```

##### REFACTOR
- Add error-bar traces from `std_` metric fields
- Accept optional `title_prefix` argument

---

#### 1.4 — File Uploader Component

**File**: `src/document_simulator/ui/components/file_uploader.py`

Responsibilities:
- `upload_single_image(label, key)` → returns `PIL.Image | None`
- `upload_multiple_images(label, key)` → returns `list[PIL.Image]`
- Validates extension (png/jpg/jpeg/bmp/tiff), shows error on invalid type

##### RED — failing tests

`tests/ui/unit/test_file_uploader.py`:
```python
import io
import pytest
import numpy as np
from PIL import Image


def _fake_uploaded_file(name: str, suffix: str = ".png"):
    """Create a minimal in-memory UploadedFile-like object."""
    img = Image.fromarray(np.full((50, 50, 3), 200, dtype=np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    class FakeFile:
        def __init__(self):
            self.name = name + suffix
            self._buf = buf

        def read(self):
            return self._buf.read()

        def getvalue(self):
            self._buf.seek(0)
            return self._buf.read()

    return FakeFile()


def test_uploaded_file_to_pil_valid():
    from document_simulator.ui.components.file_uploader import uploaded_file_to_pil
    f = _fake_uploaded_file("test", ".png")
    result = uploaded_file_to_pil(f)
    assert isinstance(result, Image.Image)


def test_uploaded_file_to_pil_returns_rgb():
    from document_simulator.ui.components.file_uploader import uploaded_file_to_pil
    f = _fake_uploaded_file("test", ".png")
    result = uploaded_file_to_pil(f)
    assert result.mode == "RGB"


def test_is_valid_image_extension_true():
    from document_simulator.ui.components.file_uploader import is_valid_image_extension
    assert is_valid_image_extension("photo.jpg") is True
    assert is_valid_image_extension("scan.PNG") is True
    assert is_valid_image_extension("doc.tiff") is True


def test_is_valid_image_extension_false():
    from document_simulator.ui.components.file_uploader import is_valid_image_extension
    assert is_valid_image_extension("data.csv") is False
    assert is_valid_image_extension("model.zip") is False


def test_uploaded_files_to_pil_list():
    from document_simulator.ui.components.file_uploader import uploaded_files_to_pil
    files = [_fake_uploaded_file(f"img{i}") for i in range(3)]
    results = uploaded_files_to_pil(files)
    assert len(results) == 3
    assert all(isinstance(r, Image.Image) for r in results)
```

##### GREEN — implementation

`src/document_simulator/ui/components/file_uploader.py`:
```python
import io
from typing import List, Optional
from PIL import Image

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}


def is_valid_image_extension(filename: str) -> bool:
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)


def uploaded_file_to_pil(uploaded_file) -> Image.Image:
    """Convert a Streamlit UploadedFile to a PIL Image (RGB)."""
    data = uploaded_file.getvalue()
    img = Image.open(io.BytesIO(data))
    return img.convert("RGB")


def uploaded_files_to_pil(uploaded_files) -> List[Image.Image]:
    return [uploaded_file_to_pil(f) for f in uploaded_files]
```

##### REFACTOR
- Return `None` (with `st.error`) for invalid extensions rather than raising
- Add `max_size_mb` guard to reject overly large uploads early

---

### Phase 2 — Augmentation Lab Page

**File**: `src/document_simulator/ui/pages/01_augmentation_lab.py`

#### 2.1 — Basic preset-based augmentation

##### RED — failing tests

`tests/ui/integration/test_augmentation_lab.py`:
```python
import pytest
from streamlit.testing.v1 import AppTest


def test_augmentation_lab_loads_without_error():
    at = AppTest.from_file(
        "src/document_simulator/ui/pages/01_augmentation_lab.py", default_timeout=30
    )
    at.run()
    assert not at.exception


def test_augmentation_lab_has_pipeline_selector():
    at = AppTest.from_file(
        "src/document_simulator/ui/pages/01_augmentation_lab.py", default_timeout=30
    )
    at.run()
    radio_labels = [r.label for r in at.radio]
    assert any("pipeline" in l.lower() or "preset" in l.lower() for l in radio_labels)


def test_augmentation_lab_has_run_button():
    at = AppTest.from_file(
        "src/document_simulator/ui/pages/01_augmentation_lab.py", default_timeout=30
    )
    at.run()
    button_labels = [b.label for b in at.button]
    assert any("augment" in l.lower() for l in button_labels)


def test_augmentation_lab_has_advanced_expander():
    at = AppTest.from_file(
        "src/document_simulator/ui/pages/01_augmentation_lab.py", default_timeout=30
    )
    at.run()
    expander_labels = [e.label for e in at.expander]
    assert any("advanced" in l.lower() or "parameter" in l.lower() for l in expander_labels)


def test_augmentation_lab_shows_download_button_after_run(monkeypatch):
    """After clicking Augment, a download button should appear."""
    import numpy as np
    from PIL import Image
    from unittest.mock import patch, MagicMock

    fake_aug = Image.fromarray(np.full((50, 50, 3), 128, dtype=np.uint8))
    mock_augmenter = MagicMock()
    mock_augmenter.augment.return_value = fake_aug

    at = AppTest.from_file(
        "src/document_simulator/ui/pages/01_augmentation_lab.py", default_timeout=30
    )
    with patch("document_simulator.augmentation.DocumentAugmenter", return_value=mock_augmenter):
        at.run()
        # Inject a fake uploaded image into session state
        at.session_state["last_uploaded_image"] = fake_aug
        # Click the augment button
        augment_btn = next(b for b in at.button if "augment" in b.label.lower())
        augment_btn.click().run()
        download_labels = [b.label for b in at.button]
        assert any("download" in l.lower() for l in download_labels)
```

##### GREEN — implementation sketch

`src/document_simulator/ui/pages/01_augmentation_lab.py`:
```python
"""Augmentation Lab — upload an image, choose a preset, see the result."""
import streamlit as st
from PIL import Image

from document_simulator.augmentation import DocumentAugmenter
from document_simulator.ui.components.file_uploader import uploaded_file_to_pil
from document_simulator.ui.components.image_display import (
    image_to_bytes,
    show_side_by_side,
)
from document_simulator.ui.state.session_state import SessionStateManager

state = SessionStateManager()

st.title("🔬 Augmentation Lab")

# ── Sidebar controls ──────────────────────────────────────────────
with st.sidebar:
    preset = st.radio(
        "Pipeline preset",
        options=["light", "medium", "heavy"],
        index=1,
        key="aug_preset",
    )

    with st.expander("Advanced parameters (12-dim action)"):
        ink_bleed_p      = st.slider("InkBleed probability",      0.0, 1.0, 0.5, 0.01)
        ink_bleed_intens = st.slider("InkBleed intensity max",     0.0, 1.0, 0.5, 0.01)
        fading_p         = st.slider("Fading probability",         0.0, 1.0, 0.3, 0.01)
        fading_val       = st.slider("Fading value max",           0.0, 1.0, 0.5, 0.01)
        markup_p         = st.slider("Markup probability",         0.0, 1.0, 0.3, 0.01)
        noise_p          = st.slider("NoiseTexturize probability", 0.0, 1.0, 0.5, 0.01)
        noise_sigma      = st.slider("NoiseTexturize sigma max",   0.0, 20.0, 5.0, 0.5)
        color_shift_p    = st.slider("ColorShift probability",     0.0, 1.0, 0.3, 0.01)
        brightness_p     = st.slider("Brightness probability",     0.0, 1.0, 0.5, 0.01)
        brightness_spr   = st.slider("Brightness spread",         0.0, 0.4, 0.2, 0.01)
        gamma_p          = st.slider("Gamma probability",          0.0, 1.0, 0.3, 0.01)
        jpeg_p           = st.slider("Jpeg probability",           0.0, 1.0, 0.4, 0.01)
        use_advanced     = st.checkbox("Use custom sliders instead of preset")

    run_btn = st.button("Augment Image", type="primary")

# ── Main area ─────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Upload a document image", type=["png", "jpg", "jpeg", "bmp", "tiff"]
)
if uploaded:
    pil_img = uploaded_file_to_pil(uploaded)
    state.set_uploaded_image(pil_img)

if run_btn:
    src = state.get_uploaded_image()
    if src is None:
        st.warning("Please upload an image first.")
    else:
        with st.spinner("Augmenting…"):
            augmenter = DocumentAugmenter(pipeline=preset)
            aug = augmenter.augment(src)
            if not isinstance(aug, Image.Image):
                from PIL import Image as _PIL
                import numpy as np
                aug = _PIL.fromarray(np.array(aug))
            state.set_aug_image(aug)

# ── Display ───────────────────────────────────────────────────────
orig = state.get_uploaded_image()
aug  = state.get_aug_image()

if orig and aug:
    show_side_by_side(orig, aug)
    st.download_button(
        "Download augmented image",
        data=image_to_bytes(aug),
        file_name="augmented.png",
        mime="image/png",
    )
elif orig:
    st.image(orig, caption="Uploaded image", use_container_width=True)
```

##### REFACTOR
- Extract `_run_augmentation(src, preset, custom_params)` function for testability
- Cache `DocumentAugmenter` construction with `@st.cache_resource`

---

### Phase 3 — OCR Engine Page

**File**: `src/document_simulator/ui/pages/02_ocr_engine.py`

#### 3.1 — Image upload → OCR → display

##### RED — failing tests

`tests/ui/integration/test_ocr_engine_page.py`:
```python
from streamlit.testing.v1 import AppTest


def test_ocr_page_loads():
    at = AppTest.from_file(
        "src/document_simulator/ui/pages/02_ocr_engine.py", default_timeout=30
    )
    at.run()
    assert not at.exception


def test_ocr_page_has_run_button():
    at = AppTest.from_file(
        "src/document_simulator/ui/pages/02_ocr_engine.py", default_timeout=30
    )
    at.run()
    labels = [b.label for b in at.button]
    assert any("ocr" in l.lower() or "run" in l.lower() for l in labels)


def test_ocr_page_has_language_selector():
    at = AppTest.from_file(
        "src/document_simulator/ui/pages/02_ocr_engine.py", default_timeout=30
    )
    at.run()
    # selectbox or text_input for language
    assert len(at.selectbox) > 0 or len(at.text_input) > 0


def test_ocr_page_shows_metrics_after_run(monkeypatch):
    """After injecting an OCR result, metric widgets should appear."""
    from unittest.mock import patch, MagicMock
    import numpy as np
    from PIL import Image

    mock_result = {
        "text": "Hello World",
        "boxes": [[[10, 5], [80, 5], [80, 25], [10, 25]]],
        "scores": [0.95],
        "raw": None,
    }
    mock_engine = MagicMock()
    mock_engine.recognize.return_value = mock_result

    at = AppTest.from_file(
        "src/document_simulator/ui/pages/02_ocr_engine.py", default_timeout=30
    )
    fake_img = Image.fromarray(np.full((50, 50, 3), 200, dtype=np.uint8))
    with patch("document_simulator.ocr.OCREngine", return_value=mock_engine):
        at.run()
        at.session_state["last_uploaded_image"] = fake_img
        at.session_state["last_ocr_result"] = mock_result
        at.run()
        metric_labels = [m.label for m in at.metric]
        assert any("confidence" in l.lower() for l in metric_labels)


def test_ocr_page_shows_region_table_after_run():
    """When OCR result is in session_state, a dataframe should be rendered."""
    from unittest.mock import patch, MagicMock
    import numpy as np
    from PIL import Image

    mock_result = {
        "text": "Invoice",
        "boxes": [[[5, 5], [60, 5], [60, 20], [5, 20]]],
        "scores": [0.88],
        "raw": None,
    }
    at = AppTest.from_file(
        "src/document_simulator/ui/pages/02_ocr_engine.py", default_timeout=30
    )
    at.run()
    at.session_state["last_ocr_result"] = mock_result
    at.run()
    assert len(at.dataframe) > 0 or len(at.table) > 0
```

##### GREEN — implementation sketch

`src/document_simulator/ui/pages/02_ocr_engine.py`:
```python
"""OCR Engine — upload a document image, extract text and see bounding boxes."""
import pandas as pd
import streamlit as st
from PIL import Image

from document_simulator.ocr import OCREngine
from document_simulator.ocr.metrics import aggregate_confidence, calculate_cer, calculate_wer
from document_simulator.ui.components.file_uploader import uploaded_file_to_pil
from document_simulator.ui.components.image_display import image_to_bytes, overlay_bboxes
from document_simulator.ui.state.session_state import SessionStateManager

state = SessionStateManager()
st.title("🔍 OCR Engine")

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    lang   = st.selectbox("Language", ["en", "ch", "fr", "de", "es"], index=0)
    use_gpu = st.checkbox("Use GPU", value=False)
    gt_file = st.file_uploader("Ground truth text (optional)", type=["txt"])
    run_btn = st.button("Run OCR", type="primary")

# ── Upload ────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Upload a document image", type=["png", "jpg", "jpeg", "bmp", "tiff"], key="ocr_upload"
)
if uploaded:
    state.set_uploaded_image(uploaded_file_to_pil(uploaded))

# ── Run OCR ───────────────────────────────────────────────────────
if run_btn:
    src = state.get_uploaded_image()
    if src is None:
        st.warning("Please upload an image first.")
    else:
        with st.spinner("Running OCR…"):
            engine = OCREngine(use_gpu=use_gpu, lang=lang)
            result = engine.recognize(src)
            state.set_ocr_result(result)

# ── Display ───────────────────────────────────────────────────────
result = state.get_ocr_result()
src    = state.get_uploaded_image()

if result and src:
    # Image with boxes
    annotated = overlay_bboxes(src, result["boxes"], result["scores"])
    st.image(annotated, caption="Detected regions", use_container_width=True)

    # Metrics row
    conf = aggregate_confidence(result["scores"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Mean Confidence", f"{conf:.3f}")
    c2.metric("Regions Detected", len(result["boxes"]))

    if gt_file:
        gt_text = gt_file.read().decode("utf-8")
        cer = calculate_cer(result["text"], gt_text)
        wer = calculate_wer(result["text"], gt_text)
        c3.metric("CER (vs GT)", f"{cer:.3f}")
        st.metric("WER (vs GT)", f"{wer:.3f}")

    # Extracted text
    st.subheader("Extracted Text")
    st.text_area("", value=result["text"], height=150, disabled=True)

    # Region table
    st.subheader("Region Details")
    rows = [
        {"#": i + 1, "Text": result["text"].split("\n")[i] if i < len(result["text"].split("\n")) else "",
         "Confidence": f"{s:.3f}"}
        for i, s in enumerate(result["scores"])
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
```

##### REFACTOR
- `@st.cache_resource` the `OCREngine` constructor (slow to initialise)
- Extract `_build_region_table(result)` → `pd.DataFrame` as standalone function

---

### Phase 4 — Batch Processing Page

**File**: `src/document_simulator/ui/pages/03_batch_processing.py`

##### RED — failing tests

`tests/ui/integration/test_batch_processing.py`:
```python
from streamlit.testing.v1 import AppTest


def test_batch_page_loads():
    at = AppTest.from_file(
        "src/document_simulator/ui/pages/03_batch_processing.py", default_timeout=30
    )
    at.run()
    assert not at.exception


def test_batch_page_has_worker_slider():
    at = AppTest.from_file(
        "src/document_simulator/ui/pages/03_batch_processing.py", default_timeout=30
    )
    at.run()
    slider_labels = [s.label for s in at.slider]
    assert any("worker" in l.lower() for l in slider_labels)


def test_batch_page_has_run_button():
    at = AppTest.from_file(
        "src/document_simulator/ui/pages/03_batch_processing.py", default_timeout=30
    )
    at.run()
    labels = [b.label for b in at.button]
    assert any("batch" in l.lower() or "run" in l.lower() for l in labels)


def test_batch_page_shows_metrics_after_processing(monkeypatch):
    """After batch run, throughput metrics should be visible."""
    from unittest.mock import patch, MagicMock
    import numpy as np
    from PIL import Image

    fake_imgs = [Image.fromarray(np.full((50, 50, 3), i * 20, dtype=np.uint8))
                 for i in range(3)]
    mock_batch = MagicMock()
    mock_batch.augment_batch.return_value = fake_imgs

    at = AppTest.from_file(
        "src/document_simulator/ui/pages/03_batch_processing.py", default_timeout=30
    )
    with patch("document_simulator.augmentation.BatchAugmenter", return_value=mock_batch):
        at.run()
        at.session_state["batch_input_images"] = fake_imgs
        at.session_state["batch_results"] = fake_imgs
        at.session_state["batch_elapsed"] = 1.5
        at.run()
        metric_labels = [m.label for m in at.metric]
        assert any(
            "processed" in l.lower() or "throughput" in l.lower() or "time" in l.lower()
            for l in metric_labels
        )
```

##### GREEN — implementation sketch

`src/document_simulator/ui/pages/03_batch_processing.py`:
```python
"""Batch Processing — augment many images at once and download the results."""
import io
import time
import zipfile

import streamlit as st

from document_simulator.augmentation import BatchAugmenter
from document_simulator.ui.components.file_uploader import uploaded_files_to_pil
from document_simulator.ui.components.image_display import image_to_bytes

st.title("⚙️ Batch Processing")

with st.sidebar:
    preset    = st.selectbox("Pipeline preset", ["light", "medium", "heavy"], index=1)
    n_workers = st.slider("Workers", min_value=1, max_value=8, value=4)
    parallel  = st.checkbox("Parallel processing", value=True)
    run_btn   = st.button("Run Batch Augmentation", type="primary")

uploaded = st.file_uploader(
    "Upload document images",
    type=["png", "jpg", "jpeg", "bmp", "tiff"],
    accept_multiple_files=True,
)

if run_btn and uploaded:
    images = uploaded_files_to_pil(uploaded)
    st.session_state["batch_input_images"] = images

    progress = st.progress(0, text="Starting…")
    t0 = time.time()
    batch = BatchAugmenter(augmenter=preset, num_workers=n_workers)
    results = batch.augment_batch(images, parallel=parallel)
    elapsed = time.time() - t0
    progress.progress(1.0, text="Done")

    st.session_state["batch_results"] = results
    st.session_state["batch_elapsed"] = elapsed

results = st.session_state.get("batch_results")
inputs  = st.session_state.get("batch_input_images")
elapsed = st.session_state.get("batch_elapsed", 0.0)

if results:
    n = len(results)
    c1, c2, c3 = st.columns(3)
    c1.metric("Processed", n)
    c2.metric("Time (s)", f"{elapsed:.1f}")
    c3.metric("Throughput", f"{n / elapsed:.1f} img/s" if elapsed > 0 else "—")

    # ZIP download
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for i, img in enumerate(results):
            zf.writestr(f"augmented_{i:04d}.png", image_to_bytes(img))
    st.download_button("Download all as ZIP", data=buf.getvalue(),
                       file_name="augmented_batch.zip", mime="application/zip")

    # Thumbnail grid
    cols = st.columns(min(n, 4))
    for i, (orig, aug) in enumerate(zip(inputs or [], results)):
        with cols[i % 4]:
            st.image(orig, caption=f"orig {i+1}", use_container_width=True)
            st.image(aug,  caption=f"aug {i+1}",  use_container_width=True)
```

##### REFACTOR
- Stream progress via a callback or per-image loop instead of waiting for full batch
- Cache `BatchAugmenter` with `@st.cache_resource(hash_funcs={...})`

---

### Phase 5 — Evaluation Dashboard Page

**File**: `src/document_simulator/ui/pages/04_evaluation.py`

##### RED — failing tests

`tests/ui/integration/test_evaluation.py`:
```python
from streamlit.testing.v1 import AppTest


def test_evaluation_page_loads():
    at = AppTest.from_file(
        "src/document_simulator/ui/pages/04_evaluation.py", default_timeout=30
    )
    at.run()
    assert not at.exception


def test_evaluation_page_has_run_button():
    at = AppTest.from_file(
        "src/document_simulator/ui/pages/04_evaluation.py", default_timeout=30
    )
    at.run()
    labels = [b.label for b in at.button]
    assert any("eval" in l.lower() or "run" in l.lower() for l in labels)


def test_evaluation_page_shows_chart_when_results_available(sample_eval_metrics):
    at = AppTest.from_file(
        "src/document_simulator/ui/pages/04_evaluation.py", default_timeout=30
    )
    at.run()
    at.session_state["eval_results"] = sample_eval_metrics
    at.run()
    # At least one plotly chart (via st.plotly_chart)
    assert len(at.plotly_chart) > 0


def test_evaluation_page_shows_summary_table(sample_eval_metrics):
    at = AppTest.from_file(
        "src/document_simulator/ui/pages/04_evaluation.py", default_timeout=30
    )
    at.run()
    at.session_state["eval_results"] = sample_eval_metrics
    at.run()
    assert len(at.dataframe) > 0 or len(at.table) > 0


def test_evaluation_page_shows_n_samples(sample_eval_metrics):
    at = AppTest.from_file(
        "src/document_simulator/ui/pages/04_evaluation.py", default_timeout=30
    )
    at.run()
    at.session_state["eval_results"] = sample_eval_metrics
    at.run()
    metric_labels = [m.label for m in at.metric]
    assert any("sample" in l.lower() for l in metric_labels)
```

##### GREEN — implementation sketch

`src/document_simulator/ui/pages/04_evaluation.py`:
```python
"""Evaluation Dashboard — measure CER/WER/confidence across a dataset."""
import pandas as pd
import streamlit as st

from document_simulator.augmentation import DocumentAugmenter
from document_simulator.evaluation import Evaluator
from document_simulator.ocr import OCREngine
from document_simulator.ui.components.metrics_charts import cer_wer_bar, confidence_box
from document_simulator.ui.state.session_state import SessionStateManager
from pathlib import Path

state = SessionStateManager()
st.title("📊 Evaluation Dashboard")

with st.sidebar:
    data_dir  = st.text_input("Dataset directory", value="./data/test")
    preset    = st.selectbox("Augmentation preset", ["light", "medium", "heavy"], index=1)
    use_gpu   = st.checkbox("GPU for OCR", value=False)
    run_btn   = st.button("Run Evaluation", type="primary")

if run_btn:
    from document_simulator.data import DocumentDataset
    p = Path(data_dir)
    if not p.exists():
        st.error(f"Directory not found: {p}")
    else:
        with st.spinner("Evaluating…"):
            augmenter = DocumentAugmenter(pipeline=preset)
            engine    = OCREngine(use_gpu=use_gpu)
            evaluator = Evaluator(augmenter, engine)
            dataset   = DocumentDataset(p)
            results   = evaluator.evaluate_dataset(dataset)
            state.set_eval_results(results)

results = state.get_eval_results()
if results:
    c1, c2 = st.columns(2)
    c1.metric("Samples", results.get("n_samples", "—"))
    c2.metric("Mean CER (augmented)", f"{results.get('mean_augmented_cer', 0):.3f}")

    # Charts
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(cer_wer_bar(results), use_container_width=True)
    with col2:
        # Placeholder — real scores need per-sample data; show bar of std instead
        st.plotly_chart(cer_wer_bar({
            "mean_original_cer":   results.get("std_original_cer", 0),
            "mean_augmented_cer":  results.get("std_augmented_cer", 0),
            "mean_original_wer":   results.get("std_original_wer", 0),
            "mean_augmented_wer":  results.get("std_augmented_wer", 0),
        }), use_container_width=True)

    # Summary table
    rows = {
        "Metric":           ["CER", "WER", "Confidence"],
        "Original (mean)":  [results.get("mean_original_cer"),
                             results.get("mean_original_wer"),
                             results.get("mean_original_confidence")],
        "Augmented (mean)": [results.get("mean_augmented_cer"),
                             results.get("mean_augmented_wer"),
                             results.get("mean_augmented_confidence")],
    }
    st.dataframe(pd.DataFrame(rows).round(4), use_container_width=True)
```

##### REFACTOR
- Store per-sample CER/WER lists in results dict for proper distribution plots
- Add `@st.cache_data` on the dataset scan step

---

### Phase 6 — RL Training Page

**File**: `src/document_simulator/ui/pages/05_rl_training.py`

This page is the most complex because training is long-running. Strategy:
- Training runs in a **background thread** with a shared queue for log entries
- UI polls the queue each `st.rerun()` cycle (using `st.empty()` placeholders)
- Stop button sets a threading `Event` that the training thread checks per checkpoint

##### RED — failing tests

`tests/ui/integration/test_rl_training.py`:
```python
from streamlit.testing.v1 import AppTest


def test_rl_training_page_loads():
    at = AppTest.from_file(
        "src/document_simulator/ui/pages/05_rl_training.py", default_timeout=30
    )
    at.run()
    assert not at.exception


def test_rl_page_has_learning_rate_input():
    at = AppTest.from_file(
        "src/document_simulator/ui/pages/05_rl_training.py", default_timeout=30
    )
    at.run()
    all_labels = (
        [s.label for s in at.slider]
        + [ti.label for ti in at.text_input]
        + [ni.label for ni in at.number_input]
    )
    assert any("learning" in l.lower() or "lr" in l.lower() for l in all_labels)


def test_rl_page_has_start_button():
    at = AppTest.from_file(
        "src/document_simulator/ui/pages/05_rl_training.py", default_timeout=30
    )
    at.run()
    labels = [b.label for b in at.button]
    assert any("start" in l.lower() or "train" in l.lower() for l in labels)


def test_rl_page_has_stop_button():
    at = AppTest.from_file(
        "src/document_simulator/ui/pages/05_rl_training.py", default_timeout=30
    )
    at.run()
    labels = [b.label for b in at.button]
    assert any("stop" in l.lower() for l in labels)


def test_rl_page_shows_reward_chart_when_log_available():
    at = AppTest.from_file(
        "src/document_simulator/ui/pages/05_rl_training.py", default_timeout=30
    )
    at.run()
    at.session_state["training_log"] = [
        {"step": 0, "reward": 0.1},
        {"step": 1000, "reward": 0.4},
        {"step": 2000, "reward": 0.6},
    ]
    at.session_state["training_running"] = False
    at.run()
    assert len(at.plotly_chart) > 0


def test_rl_page_shows_last_eval_metrics_when_log_available():
    at = AppTest.from_file(
        "src/document_simulator/ui/pages/05_rl_training.py", default_timeout=30
    )
    at.run()
    at.session_state["training_log"] = [
        {"step": 1000, "reward": 0.55, "cer": 0.08, "confidence": 0.90, "ssim": 0.72}
    ]
    at.run()
    metric_labels = [m.label for m in at.metric]
    assert any(
        "cer" in l.lower() or "reward" in l.lower() or "confidence" in l.lower()
        for l in metric_labels
    )
```

##### GREEN — implementation sketch

`src/document_simulator/ui/pages/05_rl_training.py`:
```python
"""RL Training — configure, launch, and monitor PPO training."""
import threading
import time
from pathlib import Path

import streamlit as st

from document_simulator.rl import RLConfig, RLTrainer
from document_simulator.ui.components.metrics_charts import reward_line
from document_simulator.ui.state.session_state import SessionStateManager

state = SessionStateManager()
st.title("🤖 RL Training")

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    data_dir    = st.text_input("Dataset directory", "./data/train")
    lr          = st.number_input("Learning rate", value=3e-4, format="%e")
    batch_size  = st.number_input("Batch size", value=64, step=16)
    n_steps     = st.number_input("N steps", value=2048, step=256)
    num_envs    = st.slider("Num environments", 1, 8, 4)
    total_steps = st.number_input("Total timesteps", value=100_000, step=10_000)
    ckpt_freq   = st.number_input("Checkpoint frequency", value=10_000, step=1_000)

    col1, col2 = st.columns(2)
    start_btn = col1.button("▶ Start", type="primary",
                            disabled=state.is_training_running())
    stop_btn  = col2.button("⏹ Stop",
                            disabled=not state.is_training_running())

    st.divider()
    save_btn  = st.button("💾 Save Model", disabled=state.is_training_running())
    model_file = st.file_uploader("📂 Load Model (.zip)", type=["zip"])

# ── Training thread ────────────────────────────────────────────────
_stop_event: threading.Event = st.session_state.setdefault(
    "_rl_stop_event", threading.Event()
)

def _train_thread(config: RLConfig, stop_event: threading.Event):
    """Runs in a background thread; appends log entries to session_state."""
    try:
        trainer = RLTrainer(config)

        class _LogCallback:
            def __init__(self): self.n_calls = 0
            def __call__(self, locals_, globals_):
                step   = locals_.get("self").num_timesteps
                reward = locals_.get("mean_reward", 0.0) or 0.0
                state.append_training_log({"step": step, "reward": float(reward)})
                return not stop_event.is_set()

        trainer.train(total_timesteps=int(total_steps))
        st.session_state["rl_model_path"] = str(trainer.save())
    except Exception as exc:
        st.session_state["training_error"] = str(exc)
    finally:
        state.set_training_running(False)

if start_btn:
    _stop_event.clear()
    st.session_state["training_log"] = []
    state.set_training_running(True)
    config = RLConfig(
        train_data_dir=Path(data_dir) if data_dir else None,
        learning_rate=float(lr),
        batch_size=int(batch_size),
        n_steps=int(n_steps),
        num_envs=int(num_envs),
        checkpoint_freq=int(ckpt_freq),
    )
    t = threading.Thread(target=_train_thread, args=(config, _stop_event), daemon=True)
    t.start()
    st.rerun()

if stop_btn:
    _stop_event.set()

# ── Live display ───────────────────────────────────────────────────
log = state.get_training_log()
running = state.is_training_running()

if running:
    st.info("Training in progress…")
    time.sleep(2)
    st.rerun()

if log:
    latest = log[-1]
    c1, c2, c3 = st.columns(3)
    c1.metric("Step", f"{latest['step']:,}")
    c2.metric("Reward", f"{latest.get('reward', 0):.4f}")
    c3.metric("CER", f"{latest.get('cer', '—')}")

    pct = min(latest["step"] / total_steps, 1.0) if total_steps > 0 else 0
    st.progress(pct, text=f"{latest['step']:,} / {int(total_steps):,} steps")

    st.plotly_chart(reward_line(log), use_container_width=True)

if "training_error" in st.session_state:
    st.error(f"Training error: {st.session_state['training_error']}")
```

##### REFACTOR
- Replace polling `time.sleep` + `st.rerun()` with `st.fragment` (Streamlit ≥1.37) for
  isolated auto-rerun without refreshing the whole page
- Persist training log to a JSON file so it survives page reloads

---

### Phase 7 — Home Page, Settings, and Polish

**Files**:
- `src/document_simulator/ui/app.py` — Home page with quick-start widget
- Update `pyproject.toml` with `ui` extra and launch script
- `tests/ui/e2e/test_full_flow.py`

#### 7.1 — Home page

##### RED — failing tests

`tests/ui/e2e/test_full_flow.py`:
```python
from streamlit.testing.v1 import AppTest


def test_home_page_loads():
    at = AppTest.from_file("src/document_simulator/ui/app.py", default_timeout=30)
    at.run()
    assert not at.exception


def test_home_page_has_title():
    at = AppTest.from_file("src/document_simulator/ui/app.py", default_timeout=30)
    at.run()
    titles = [t.value for t in at.title]
    assert any("document" in t.lower() or "simulator" in t.lower() for t in titles)


def test_home_page_has_nav_links():
    at = AppTest.from_file("src/document_simulator/ui/app.py", default_timeout=30)
    at.run()
    # Navigation links rendered as st.page_link or st.link_button
    assert len(at.button) > 0 or len(at.markdown) > 0


def test_home_page_quick_augment_button():
    at = AppTest.from_file("src/document_simulator/ui/app.py", default_timeout=30)
    at.run()
    labels = [b.label for b in at.button]
    assert any("augment" in l.lower() or "quick" in l.lower() for l in labels)
```

##### GREEN — implementation sketch

`src/document_simulator/ui/app.py`:
```python
"""Document Simulator — Streamlit entry point."""
import streamlit as st

st.set_page_config(
    page_title="Document Simulator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📄 Document Simulator")
st.caption("Document image augmentation · OCR · RL Optimisation")
st.divider()

# Quick nav cards
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown("### 🔬 Augmentation Lab")
    st.caption("Upload, augment, download")
    st.page_link("pages/01_augmentation_lab.py", label="Open →")
with col2:
    st.markdown("### 🔍 OCR Engine")
    st.caption("Extract text + bounding boxes")
    st.page_link("pages/02_ocr_engine.py", label="Open →")
with col3:
    st.markdown("### ⚙️ Batch Processing")
    st.caption("Augment many images at once")
    st.page_link("pages/03_batch_processing.py", label="Open →")
with col4:
    st.markdown("### 📊 Evaluation")
    st.caption("CER / WER / Confidence charts")
    st.page_link("pages/04_evaluation.py", label="Open →")
with col5:
    st.markdown("### 🤖 RL Training")
    st.caption("Learn optimal aug parameters")
    st.page_link("pages/05_rl_training.py", label="Open →")

st.divider()

# Quick-start single image augment
st.subheader("Quick Augment")
uploaded = st.file_uploader(
    "Drop an image here to augment immediately",
    type=["png", "jpg", "jpeg", "bmp", "tiff"],
    key="home_upload",
)
quick_btn = st.button("Augment →", type="primary", disabled=uploaded is None)

if quick_btn and uploaded:
    from PIL import Image
    import io
    from document_simulator.augmentation import DocumentAugmenter
    from document_simulator.ui.components.image_display import show_side_by_side, image_to_bytes
    from document_simulator.ui.components.file_uploader import uploaded_file_to_pil

    with st.spinner("Augmenting…"):
        pil = uploaded_file_to_pil(uploaded)
        aug = DocumentAugmenter(pipeline="medium").augment(pil)
        if not isinstance(aug, Image.Image):
            aug = Image.fromarray(aug)
        show_side_by_side(pil, aug)
        st.download_button(
            "Download augmented", data=image_to_bytes(aug),
            file_name="augmented.png", mime="image/png",
        )


def launch():
    """Entry point for `document-simulator-ui` script."""
    import subprocess, sys
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run",
         __file__, "--server.headless", "true"],
        check=True,
    )
```

---

## 7. Running Tests

### Fast (no OCR/RL deps)

```bash
uv run pytest tests/ui/ -q --no-cov
```

### All UI tests verbose

```bash
uv run pytest tests/ui/ -v
```

### Single page integration test

```bash
uv run pytest tests/ui/integration/test_augmentation_lab.py -v
```

### Full suite including core package

```bash
uv run pytest -m "not slow" -q
```

---

## 8. Acceptance Criteria

| Phase | Criterion |
|-------|-----------|
| 1 | All unit tests in `tests/ui/unit/` pass; `SessionStateManager`, `overlay_bboxes`, `cer_wer_bar`, `uploaded_file_to_pil` importable |
| 2 | Augmentation Lab loads, preset selector present, Augment button present, download button appears after run |
| 3 | OCR page loads, Run OCR button present, metric widgets visible when result in state, region dataframe visible |
| 4 | Batch page loads, worker slider present, ZIP download button appears after run |
| 5 | Evaluation page loads, plotly chart and dataframe visible when eval results in state |
| 6 | RL Training page loads, Start/Stop buttons present, reward chart visible when training log in state |
| 7 | Home page loads, nav links present, Quick Augment button present |
| All | `uv run pytest tests/ui/ -q` exits 0 with 0 failures |

---

## 9. Future Enhancements (out of scope for this plan)

- **Live TensorBoard embed** (`st.components.v1.iframe`) inside the RL Training page
- **Annotation editor** — click to add/edit ground truth bounding boxes on an image
- **Dataset browser** — paginated gallery of image/ground-truth pairs
- **Model comparison** — load two `.zip` models and compare reward curves side-by-side
- **Docker deployment** — `Dockerfile` + `docker-compose.yml` for one-command launch
- **Auth gate** — `streamlit-authenticator` wrapper for shared deployments
