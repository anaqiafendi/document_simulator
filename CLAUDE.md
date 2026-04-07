# CLAUDE.md - Document Simulator

This file provides guidance to Claude Code and AI assistants when working with the **document_simulator** codebase.

## Project Overview

**Document Simulator** is a comprehensive Python system for document image augmentation, OCR training, and reinforcement learning-based pipeline optimization. It's designed to:

- **Generate realistic document degradation** through Augraphy transformations
- **Train and fine-tune OCR models** using PaddleOCR with custom datasets
- **Optimize document processing pipelines** using Stable-Baselines3 RL agents
- **Evaluate document quality** with multiple metrics (CER, WER, BLEU)
- **Support multiple document types** (receipts, forms, handwritten, printed text)

### Core Philosophy

- **Modularity**: Clean separation between augmentation, OCR, and RL components
- **Configurability**: All settings via `.env` and Pydantic Settings
- **Extensibility**: Custom augmentation strategies, RL rewards, and metrics
- **Production-Ready**: GPU acceleration, experiment tracking, detailed logging
- **AI-Friendly**: Type hints, comprehensive docstrings, clear data structures

---

## Environment

- **Python**: 3.10, 3.11, or 3.12 (3.11 recommended, pinned in `.python-version`)
- **Package Manager**: `uv` — always use `uv run` or `uv pip` instead of bare `python`/`pip`
- **Source Layout**: Main package under `src/document_simulator/`:
  - `src/document_simulator/augmentation/` — Augraphy integration
  - `src/document_simulator/ocr/` — PaddleOCR engine
  - `src/document_simulator/rl/` — Stable-Baselines3 training
  - `src/document_simulator/data/` — Dataset loaders and ground truth parsers
  - `src/document_simulator/evaluation/` — Evaluator (CER/WER/confidence across datasets)
  - `src/document_simulator/utils/` — Shared utilities (ImageHandler)
  - `src/document_simulator/ui/` — **SUNSETTED** Streamlit UI (do not modify)
  - `src/document_simulator/api/` — FastAPI backend (serves React SPA + all API routes)
  - `webapp/` — **CURRENT** React + TypeScript frontend (Vite, React Router, Recharts)
  - `src/document_simulator/cli.py` — CLI entry point

### Quick Setup

```bash
# Clone/navigate to project
cd document_simulator

# Automated setup (recommended)
chmod +x setup.sh
./setup.sh

# OR manual setup
uv python pin 3.11                    # Pin Python version
uv venv                               # Create virtual environment
uv sync                               # Install core dependencies
uv sync --extra dev                   # Add dev tools (pytest, black, ruff, mypy)
uv sync --extra ui                    # Add Streamlit + Plotly for the web UI
uv sync --all-extras                  # Install everything (dev + ui + notebook + docs)

# Create necessary directories
mkdir -p data models output logs cache checkpoints

# Configure environment
cp .env.example .env
# Edit .env with your settings (see docs/environment-setup.md)
```

> **Network note**: If `uv sync` fails with TLS/SSL errors, append `--native-tls`.

---

## Key Commands

```bash
# Environment setup & management
uv venv && uv sync                    # Create venv and install core deps
uv sync --extra dev                   # Add dev tools (pytest, black, ruff, mypy)
uv sync --extra ui                    # Add Streamlit + Plotly for the web UI
uv sync --extra notebook              # Add Jupyter notebook support
uv sync --all-extras                  # Install everything
uv tree                               # View dependency tree

# Run the Streamlit UI
uv run streamlit run src/document_simulator/ui/app.py
# or, after uv sync --extra ui, via the installed script:
document-simulator-ui

# Run the CLI
uv run python -m document_simulator --help
uv run python -m document_simulator augment input.jpg output.jpg
uv run python -m document_simulator augment input.jpg output.jpg --pipeline heavy
uv run python -m document_simulator ocr document.jpg
uv run python -m document_simulator train --data-dir ./data/train --num-steps 100000

# Testing (core package)
uv run pytest -m "not slow" -q               # Fast tests (no RL training)
uv run pytest                                # All tests including slow
uv run pytest tests/unit/ -v                 # Unit tests only
uv run pytest tests/integration/ -v          # Integration tests only

# Testing (Streamlit UI)
uv run pytest tests/ui/ -q --no-cov          # All UI tests (fast, uses AppTest)
uv run pytest tests/ui/unit/ -q --no-cov     # Unit tests for components
uv run pytest tests/ui/integration/ -v       # Integration tests per page
uv run pytest tests/ui/e2e/ -v               # End-to-end home page tests

# Single test file
uv run pytest tests/ui/integration/test_augmentation_lab.py -v

# Code Quality
uv run black .                        # Format code (line-length=100)
uv run ruff check .                   # Lint code
uv run ruff check . --fix             # Lint and auto-fix
uv run mypy src/                      # Type check
uv run pre-commit install             # Install git hooks
uv run pre-commit run --all-files     # Run all hooks
```

---

## Architecture

### System Design

The system combines three major subsystems into a unified data processing pipeline:

```
┌─────────────────────────────────────────┐
│      INPUT: Document Images             │
│  (PNG, JPG, PDF, real scans)            │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│   1. AUGMENTATION PIPELINE              │
│      (Augraphy + Custom Transforms)     │
│                                         │
│  • Ink Phase: InkBleed, Fading, Markup │
│  • Paper Phase: Noise, Wrinkles, etc   │
│  • Post Phase: Blur, Brightness, JPEG  │
│  • Custom: Rotation, Perspective, etc  │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│   2. OCR ENGINE                         │
│      (PaddleOCR + Preprocessing)        │
│                                         │
│  • Text Detection (CRAFT, DB)           │
│  • Text Recognition (CRNNx)             │
│  • Post-processing (confidence, etc)    │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│   3. RL OPTIMIZATION                    │
│      (Stable-Baselines3)                │
│                                         │
│  • Gymnasium Environment                │
│  • PPO / DQN Agent                      │
│  • Reward: Quality vs Realism Trade-off │
│  • Training with TensorBoard & W&B      │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│      OUTPUT: Optimized Pipeline         │
│  (Best augmentation parameters found)   │
└─────────────────────────────────────────┘
```

### Module Structure

#### `src/document_simulator/augmentation/`
Wraps and extends **Augraphy** for realistic document degradation.

- **`augmenter.py`** — Main `DocumentAugmenter` class
  - Method: `augment(image: PIL.Image | np.ndarray) → (augmented, metadata)`
  - Applies transformations in three sequential phases
  - Returns same type as input (PIL or numpy)
  - Configurable via `AugmentationConfig` Pydantic model

- **`strategies.py`** — Custom augmentation strategies
  - `InkDegradationStrategy` — Simulate fading pen/ink
  - `PaperArtifactStrategy` — Add creases, stains, watermarks
  - `ProcessingArtifactStrategy` — Blur, noise, compression
  - Base `AugmentationStrategy` for custom implementations

- **`config.py`** — Configuration for each augmentation phase
  - Pydantic models: `InkPhaseConfig`, `PaperPhaseConfig`, `PostPhaseConfig`
  - Controls intensity, probability, and specific transforms per phase

#### `src/document_simulator/ocr/`
Integrates **PaddleOCR** with custom preprocessing and post-processing.

- **`engine.py`** — Main `OCREngine` class
  - Methods: `detect()` (bounding boxes), `recognize()` (text), `recognize_full()` (combined)
  - Supports CPU and GPU execution (`use_gpu` param or `PADDLEOCR_USE_GPU=true` in `.env`)
  - Returns: `OCRResult` with bounding boxes, text, confidence scores
  - Language support: `PADDLEOCR_LANG` in `.env`

- **`preprocessor.py`** — Image preprocessing for better OCR
  - Contrast enhancement, deskewing, noise reduction
  - CLAHE, Otsu thresholding, morphological operations

- **`postprocessor.py`** — Result refinement
  - Confidence filtering, duplicate removal, alignment
  - Metrics: CER (Character Error Rate), WER (Word Error Rate), Levenshtein

#### `src/document_simulator/rl/`
**Stable-Baselines3** integration for pipeline optimization.

- **`environment.py`** — Custom Gymnasium environment `DocumentEnv`
  - Action space: Augmentation parameter selections
  - Observation space: Document features (texture, contrast, etc)
  - Reward function: Balances OCR quality vs visual realism
  - Configurable via `EnvConfig` Pydantic model

- **`optimizer.py`** — Main `PipelineOptimizer` class
  - Methods: `train(episodes)`, `optimize(image) → best_params`
  - Wraps PPO, DQN, or other SB3 algorithms
  - Checkpointing and model loading
  - Integration with TensorBoard and W&B logging

- **`rewards.py`** — Reward function definitions
  - `quality_reward()` — Based on OCR character accuracy
  - `realism_reward()` — Based on visual similarity to originals
  - `combined_reward()` — Weighted sum with configurable trade-off

#### `src/document_simulator/models/`
Model definitions and checkpointing.

- **`base.py`** — Abstract base classes for all models
- **`checkpoint.py`** — Save/load trained models, metadata, config
- **`registry.py`** — Model registration and discovery

#### `src/document_simulator/data/`
Dataset loading and ground truth parsing.

- **`loaders.py`** — Dataset readers
  - `ICDARDataset` — ICDAR 2013, 2015, 2017 benchmarks
  - `SROIEDataset` — Scanned Receipts OCR
  - `CustomDataset` — User-provided image + ground truth pairs
  - Methods: `__len__()`, `__getitem__()` for PyTorch compatibility

- **`parsers.py`** — Ground truth format parsers
  - JSON, XML, TXT formats
  - Converts to standardized `GroundTruth` objects
  - Extracts bounding boxes, text, metadata

#### `src/document_simulator/utils/`
Shared utilities and metrics.

- **`metrics.py`** — Evaluation metrics
  - `character_error_rate()` — CER
  - `word_error_rate()` — WER
  - `bleu_score()` — BLEU (borrowed from NMT)
  - `levenshtein_distance()` — Edit distance

- **`visualization.py`** — Plotting and debugging
  - `visualize_augmentation()` — Before/after comparison
  - `visualize_ocr_results()` — Bounding boxes overlay
  - `plot_training_curves()` — Loss, reward, accuracy

- **`logging.py`** — Structured logging setup
  - Loguru configuration
  - TensorBoard and W&B integration

#### `src/document_simulator/cli.py`
Click CLI with subcommands:
- `augment` — Apply augmentations to image directory
- `ocr` — Run OCR on single image
- `train` — Train RL agent
- `evaluate` — Evaluate model on benchmark dataset

---

## UI Architecture

> **IMPORTANT FOR AI AGENTS**: The **React/TypeScript webapp** (`webapp/`) is the **current, active frontend**. The Streamlit UI (`src/document_simulator/ui/`) is **SUNSETTED — do NOT add features or modify it**. All new UI work goes in `webapp/`.

---

### Current Frontend: React + TypeScript Webapp (`webapp/`)

**Stack**: React 18, TypeScript 5.5, Vite, React Router v7, Recharts, React-Konva (canvas drawing), `@faker-js/faker`

**Launch**:
```bash
# Backend (FastAPI serves both API and React SPA)
uv run uvicorn src.document_simulator.api.main:app --reload --port 8000

# Frontend dev server (proxies /api/* to :8000)
cd webapp && npm run dev
# Open: http://localhost:5173
```

**File layout**:
```
webapp/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── src/
    ├── App.tsx                   # React Router routes (see route list below)
    ├── SyntheticGenerator.tsx    # Main generator page (template upload, zone canvas, respondents, preview)
    ├── main.tsx                  # Entry point
    ├── api/
    │   └── client.ts             # fetch-based API client — all /api/* calls go here
    ├── components/
    │   ├── BatchGeneratePanel.tsx
    │   ├── ConfigPanel.tsx
    │   ├── FontSelect.tsx
    │   ├── InkColorPicker.tsx
    │   ├── NavBar.tsx
    │   ├── PreviewGallery.tsx
    │   ├── RespondentPanel.tsx
    │   ├── StatusBar.tsx
    │   ├── ZoneCanvas.tsx        # React-Konva canvas for zone drawing
    │   └── ZoneList.tsx
    ├── hooks/
    │   ├── useGenerate.ts
    │   ├── usePreviews.ts
    │   ├── useRespondents.ts
    │   ├── useTemplate.ts
    │   ├── useZonePreview.ts
    │   └── useZones.ts
    ├── pages/
    │   ├── AugmentationLab.tsx   # Augmentation presets + intensity sliders
    │   ├── BatchProcessing.tsx
    │   ├── Evaluation.tsx
    │   ├── OcrEngine.tsx
    │   └── RlTraining.tsx
    ├── types/
    │   └── index.ts              # All shared TypeScript types
    └── utils/
        ├── colors.ts
        └── faker.ts
```

**Routes** (`App.tsx`):
- `/` → `SyntheticGenerator`
- `/augmentation` → `AugmentationLab`
- `/ocr` → `OcrEngine`
- `/batch` → `BatchProcessing`
- `/evaluation` → `Evaluation`
- `/rl` → `RlTraining`

**API client pattern** (`webapp/src/api/client.ts`):
- `BASE = ''` (relative — proxied by Vite in dev, served directly in prod)
- Key endpoints: `/api/template`, `/api/samples`, `/api/preview`, `/api/generate`, `/api/jobs/:id`, `/api/augmentation/*`, `/api/ocr/recognize`, `/api/batch/*`, `/api/evaluation/*`, `/api/rl/*`, `/api/synthesis/*`
- Always add new endpoint functions to `client.ts`

**TypeScript conventions**:
- Functional components with typed props
- Custom hooks in `hooks/` for stateful logic (keep components lean)
- Shared types in `types/index.ts`
- Inline styles are acceptable; no CSS framework in use
- Use `recharts` for charts, `react-konva` for canvas

**Adding a new page**:
1. Create `webapp/src/pages/MyPage.tsx`
2. Add route in `App.tsx`
3. Add nav link in `components/NavBar.tsx`
4. Add API calls in `webapp/src/api/client.ts`
5. Add corresponding FastAPI router in `src/document_simulator/api/routers/`

---

### Backend API (`src/document_simulator/api/`)

FastAPI app that serves the React SPA and all backend routes.

```
api/
├── app.py          # FastAPI app, mounts routers, serves React SPA from webapp/dist/
├── models.py       # Pydantic request/response models
├── jobs.py         # Background job tracking
└── routers/
    ├── augmentation.py
    ├── batch.py
    ├── evaluation.py
    ├── ocr.py
    ├── rl_training.py
    └── synthesis.py    # Template upload, zone preview, generate, sample
```

**Launch backend**:
```bash
uv run uvicorn src.document_simulator.api.main:app --reload --port 8000
```

---

### SUNSETTED: Streamlit UI (`src/document_simulator/ui/`)

> **DO NOT MODIFY.** The Streamlit UI has been superseded by the React webapp. It remains in the repository for historical reference only. Do not add features, fix bugs, or write tests for it. All UI work belongs in `webapp/`.

The Streamlit UI tests (`tests/ui/`) are also frozen — do not add to them.

---

## Key Design Decisions

### 1. **MyPy Configuration (Lenient)**
- `disallow_untyped_defs = false` — Type hints not strictly required
- `check_untyped_defs = true` — But existing annotations are validated
- External libs (`augraphy`, `paddleocr`, `stable_baselines3`, `cv2`, `albumentations`) set to `ignore_missing_imports = true`
- This provides flexibility for rapid development while catching annotation bugs

### 2. **Ruff Ignores E501 (Line Length)**
- Black handles line length enforcement at 100 characters
- Ruff doesn't duplicate this check (E501 ignored)
- Consistent formatting: `uv run black .`

### 3. **NumPy < 2.0 Pinned**
- PaddleOCR and PaddlePaddle require NumPy < 2.0
- Prevents runtime incompatibilities
- Will be updated once PaddlePaddle supports NumPy 2.0

### 4. **GPU-Agnostic Design**
- All GPU code is optional (`use_gpu=True` parameter)
- Falls back to CPU automatically if no GPU available
- Configuration via environment: `PADDLEOCR_USE_GPU=true`
- No hard dependency on CUDA/cuDNN (detect at runtime)

### 5. **Pydantic for Everything**
- All data structures inherit from `BaseModel`
- Automatic validation, JSON serialization, schema generation
- Settings loaded from `.env` via `pydantic.settings.BaseSettings`

### 6. **Experiment Tracking**
- TensorBoard for RL training visualization (default)
- Weights & Biases (W&B) optional for cloud experiment tracking
- Configuration: `WANDB_PROJECT` in `.env`
- Metrics logged: loss, reward, accuracy, augmentation params

---

## Development Workflow

### Test-Driven Development (TDD)

**Step 1: Write Failing Test (RED)**
```python
# tests/unit/test_augmentation.py
import pytest
from src.document_simulator.augmentation.strategies import CustomBlurStrategy

def test_custom_blur_strategy():
    """Test custom blur augmentation"""
    strategy = CustomBlurStrategy(kernel_size=5)
    image = pytest.sample_image()
    augmented = strategy.apply(image)
    assert augmented.size == image.size
    assert augmented != image
```

**Step 2: Implement (GREEN)**
```python
# src/document_simulator/augmentation/strategies.py
from PIL import ImageFilter

class CustomBlurStrategy(AugmentationStrategy):
    def __init__(self, kernel_size: int = 5):
        self.kernel_size = kernel_size
    
    def apply(self, image):
        return image.filter(ImageFilter.GaussianBlur(radius=self.kernel_size))
```

**Step 3: Refactor**
- Add error handling, logging, type hints
- Add docstring with example
- Update configuration model
- Add integration test

### Test Organization

```
tests/
├── unit/                               # Fast, isolated tests
│   ├── test_augmentation.py
│   ├── test_ocr_engine.py
│   ├── test_rl_env.py
│   ├── test_models.py
│   ├── test_data_loaders.py
│   └── test_config.py
│
├── integration/                        # Module interactions (slower)
│   ├── test_augmentation_ocr.py
│   ├── test_ocr_evaluation.py
│   └── test_rl_training.py
│
└── e2e/                                # End-to-end (slowest)
    └── test_full_pipeline.py
```

---

## Code Conventions

### Type Hints
```python
# Good: Functions have clear signatures
def augment(
    image: PIL.Image | np.ndarray,
    config: AugmentationConfig,
) -> tuple[PIL.Image | np.ndarray, dict]:
    """Augment document image."""
    ...
```

### Docstrings (Google-Style)
```python
def evaluate_ocr(
    predicted: str,
    ground_truth: str,
    metric: str = "cer",
) -> float:
    """Calculate OCR evaluation metric.
    
    Args:
        predicted: OCR output text.
        ground_truth: Reference text.
        metric: "cer" or "wer".
    
    Returns:
        Error rate between 0 and 1.
    
    Raises:
        ValueError: If metric is invalid.
    """
```

### Logging
```python
from loguru import logger

logger.debug(f"Processing {len(images)} images")
logger.info(f"Training epoch {epoch}: reward={reward:.3f}")
logger.warning(f"Low OCR confidence: {conf:.2%}")
logger.error(f"Failed to load: {error}", exc_info=True)
```

### Error Handling
```python
try:
    augmented = augment(image)
except AugmentationError as e:
    logger.error(f"Augmentation failed: {e}", exc_info=True)
    raise
```

---

## Configuration Reference

### .env File

```bash
# Data & Output Paths
DATA_DIR=./data
MODELS_DIR=./models
OUTPUT_DIR=./output
CACHE_DIR=./cache

# Augmentation Settings
AUGMENT_INTENSITY=0.7
ENABLE_WATERMARK=true
ROTATION_RANGE=15

# OCR Settings
PADDLEOCR_USE_GPU=false
PADDLEOCR_LANG=en
OCR_CONFIDENCE_THRESHOLD=0.5
BATCH_SIZE=32

# RL Training Settings
NUM_EPOCHS=100
LEARNING_RATE=1e-4
RL_ALGORITHM=ppo
REWARD_QUALITY_WEIGHT=0.6
REWARD_REALISM_WEIGHT=0.4

# Experiment Tracking
WANDB_PROJECT=document-simulator
LOG_LEVEL=INFO
```

---

## Common Tasks

### Adding a New Dataset Loader

1. Create in `src/document_simulator/data/loaders.py`
2. Add unit test in `tests/unit/test_data_loaders.py`
3. Add integration test with augmentation + OCR
4. Update `docs/` if new format

### Tuning RL Agent

1. Adjust reward function in `src/document_simulator/rl/rewards.py`
2. Adjust environment in `src/document_simulator/rl/environment.py`
3. Modify hyperparameters in `.env`
4. Monitor with TensorBoard: `tensorboard --logdir=./logs`

### Running Full Pipeline

```bash
# Augment images
uv run python -m document_simulator augment \
    --input data/original/ \
    --output data/augmented/

# Run OCR
uv run python -m document_simulator ocr \
    --image data/augmented/sample.jpg

# Train RL agent
uv run python -m document_simulator train \
    --dataset data/augmented/ \
    --epochs 100

# Evaluate
uv run python -m document_simulator evaluate \
    --dataset icdar2015 \
    --output results.json
```

---

## Resources & References

- **Augraphy**: https://github.com/sparkfish/augraphy
- **PaddleOCR**: https://github.com/PaddlePaddle/PaddleOCR
- **Stable-Baselines3**: https://stable-baselines3.readthedocs.io/
- **Gymnasium**: https://gymnasium.farama.org/
- **Pydantic**: https://docs.pydantic.dev/

---

## Quick Reference

| Task | Command |
|------|---------|
| Setup (core) | `./setup.sh` or `uv venv && uv sync` |
| Setup (UI) | `uv sync --extra ui` |
| Launch UI | `uv run streamlit run src/document_simulator/ui/app.py` |
| All tests | `uv run pytest -m "not slow" -q` |
| UI tests only | `uv run pytest tests/ui/ -q --no-cov` |
| Unit tests | `uv run pytest tests/unit/ -v` |
| Format | `uv run black .` |
| Lint | `uv run ruff check . --fix` |
| Type check | `uv run mypy src/` |
| Coverage | `uv run pytest --cov=document_simulator --cov-report=html` |
| TensorBoard | `tensorboard --logdir=./logs` |

## Known Package Quirks

- **augraphy 8.2.6** (only version available): no `Fading` class — use `LowLightNoise`.
  `ColorShift` takes `color_shift_offset_x_range` / `color_shift_offset_y_range` separately.
- **SB3 CnnPolicy**: observation space must be `dtype=np.uint8` with shape `(H, W, C)`.
- **NumPy < 2.0** pinned for PaddlePaddle compatibility.
- **augraphy writes cache** to `augraphy_cache/` at repo root (covered in `.gitignore`).

---

**Last Updated**: 2026-03-01  
**Project Status**: Early Alpha  
**Python Version**: 3.10, 3.11, 3.12  
**Package Manager**: uv
