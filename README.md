# Document Simulator

> **Document image augmentation and OCR training system** using Augraphy, PaddleOCR, and Stable-Baselines3

Generate realistic degraded document images, extract text with OCR, and use reinforcement learning to discover the augmentation parameters that best stress-test your extraction pipeline.

---

## Quick Start

```bash
# 1. Install uv (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone and set up
git clone https://github.com/yourusername/document-simulator.git
cd document-simulator
uv venv && uv sync
mkdir -p data models output logs cache checkpoints
cp .env.example .env

# 3. Verify
uv run python -c "import augraphy, torch, stable_baselines3; print('All packages OK')"
```

### Try it immediately

**Augment a document image:**
```bash
uv run python -m document_simulator augment input.jpg output.jpg
uv run python -m document_simulator augment input.jpg output.jpg --pipeline heavy
```

**Run OCR on a document:**
```bash
uv run python -m document_simulator ocr document.jpg
uv run python -m document_simulator ocr document.jpg --output extracted.txt
```

**Train the RL optimiser:**
```bash
uv run python -m document_simulator train --data-dir ./data --num-steps 100000
```

**Run the test suite:**
```bash
uv sync --extra dev
uv run pytest -m "not slow" -q
```

---

## Architecture

The system is built from three composable subsystems. Each can be used independently or wired together through the RL optimisation layer.

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Document Simulator                             │
│                                                                        │
│  Input: any document image (PNG / JPG / scanned PDF page)             │
│                              │                                         │
│              ┌───────────────▼────────────────┐                       │
│              │      1. AUGMENTATION PIPELINE   │                       │
│              │         (Augraphy)              │                       │
│              │                                 │                       │
│              │  Ink Phase                      │                       │
│              │  ├─ InkBleed   (p, intensity)   │                       │
│              │  ├─ LowLight   (p, noise)       │                       │
│              │  └─ Markup     (p, lines)       │                       │
│              │                                 │                       │
│              │  Paper Phase                    │                       │
│              │  ├─ NoiseTexturize (p, sigma)   │                       │
│              │  └─ ColorShift    (p, offset)   │                       │
│              │                                 │                       │
│              │  Post Phase                     │                       │
│              │  ├─ Brightness  (p, range)      │                       │
│              │  ├─ Gamma       (p, gamma)      │                       │
│              │  ├─ Dithering   (p)             │                       │
│              │  └─ Jpeg        (p, quality)    │                       │
│              │                                 │                       │
│              │  Presets: light / medium / heavy│                       │
│              └───────────────┬─────────────────┘                       │
│                              │ augmented image                         │
│              ┌───────────────▼─────────────────┐                       │
│              │      2. OCR ENGINE              │                       │
│              │         (PaddleOCR)             │                       │
│              │                                 │                       │
│              │  ├─ Text Detection (bboxes)     │                       │
│              │  ├─ Text Recognition (chars)    │                       │
│              │  └─ Confidence Scores           │                       │
│              │                                 │                       │
│              │  Metrics                        │                       │
│              │  ├─ CER  (Character Error Rate) │                       │
│              │  ├─ WER  (Word Error Rate)      │                       │
│              │  └─ Mean Confidence             │                       │
│              └───────────────┬─────────────────┘                       │
│                              │ quality signal                          │
│              ┌───────────────▼─────────────────┐                       │
│              │      3. RL OPTIMISATION         │                       │
│              │         (Stable-Baselines3)     │                       │
│              │                                 │                       │
│              │  DocumentEnv (Gymnasium)        │                       │
│              │  ├─ Observation: image (uint8)  │                       │
│              │  ├─ Action: 12 aug params       │                       │
│              │  └─ Reward: 0.5×CAR            │                       │
│              │           + 0.3×confidence      │                       │
│              │           + 0.2×(1−SSIM)        │                       │
│              │                                 │                       │
│              │  PPO agent + CnnPolicy          │                       │
│              │  CheckpointCallback             │                       │
│              │  EvalCallback → best_model.zip  │                       │
│              └─────────────────────────────────┘                       │
│                                                                        │
│  Output: augmented images + OCR results + trained RL model            │
└──────────────────────────────────────────────────────────────────────┘
```

### Data flow

```
Document Image
      │
      ├──► BatchAugmenter ──────────────────────────────► Augmented Dataset
      │         │                                               │
      │    PresetFactory                               DocumentDataset
      │    light/medium/heavy                         (image + GroundTruth)
      │
      ├──► OCREngine.recognize()
      │         │
      │    {text, boxes, scores}
      │         │
      │    calculate_cer() / calculate_wer()
      │    aggregate_confidence()
      │
      └──► DocumentEnv.step(action)
                │
           RLTrainer (PPO)
                │
           best_model.zip
```

### Module map

| Module | Key class | Responsibility |
|--------|-----------|---------------|
| `augmentation/presets.py` | `PresetFactory` | light / medium / heavy Augraphy configs |
| `augmentation/augmenter.py` | `DocumentAugmenter` | single-image augmentation, PIL ↔ numpy |
| `augmentation/batch.py` | `BatchAugmenter` | multiprocessing batch + directory processing |
| `ocr/engine.py` | `OCREngine` | PaddleOCR wrapper, CPU/GPU, path/PIL/numpy input |
| `ocr/metrics.py` | functions | CER, WER, Levenshtein, confidence aggregation |
| `data/ground_truth.py` | `GroundTruthLoader` | JSON + ICDAR XML annotation parsing |
| `data/datasets.py` | `DocumentDataset` | PyTorch Dataset with train/val/test split |
| `rl/environment.py` | `DocumentEnv` | Gymnasium env, 12-dim action, composite reward |
| `rl/trainer.py` | `RLTrainer` + `RLConfig` | PPO training loop, callbacks, save/load |
| `evaluation/evaluator.py` | `Evaluator` | dataset-level CER/WER/confidence aggregation |
| `utils/image_io.py` | `ImageHandler` | load from path / PIL / numpy / bytes |
| `cli.py` | `main()` | `augment` / `ocr` / `train` subcommands |

---

## Installation

### Prerequisites

- Python 3.10, 3.11, or 3.12 (3.11 recommended)
- 8 GB+ RAM (16 GB+ for RL training)
- Optional: CUDA-capable GPU

### Option A — automated

```bash
chmod +x setup.sh && ./setup.sh
```

### Option B — manual

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create environment and install
uv venv && uv sync
uv sync --extra dev        # pytest, black, ruff, mypy
uv sync --extra notebook   # Jupyter

# Runtime directories (gitignored)
mkdir -p data models output logs cache checkpoints

# Environment config
cp .env.example .env
```

### Verify

```bash
uv run python -c "
import augraphy, torch, stable_baselines3, paddleocr, cv2
print('augraphy  :', augraphy.__version__)
print('torch     :', torch.__version__)
print('SB3       :', stable_baselines3.__version__)
print('CUDA      :', torch.cuda.is_available())
"
```

---

## Usage

### Python API

**Augmentation**
```python
from document_simulator.augmentation import DocumentAugmenter, BatchAugmenter, PresetFactory

# Single image — returns same type as input (PIL or numpy)
augmenter = DocumentAugmenter(pipeline="light")   # light | medium | heavy | default
result = augmenter.augment(image)

# Batch — parallel multiprocessing
batch = BatchAugmenter(num_workers=4)
augmented_images = batch.augment_batch(images)
batch.augment_directory(Path("data/raw"), Path("data/augmented"))
```

**OCR**
```python
from document_simulator.ocr import OCREngine, calculate_cer, calculate_wer

ocr = OCREngine(use_gpu=False, lang="en")
result = ocr.recognize("document.jpg")   # also accepts PIL Image or numpy array
# result = {"text": "...", "boxes": [...], "scores": [...]}

cer = calculate_cer(result["text"], ground_truth)
wer = calculate_wer(result["text"], ground_truth)
```

**Data loading**
```python
from document_simulator.data import DocumentDataset, GroundTruthLoader

dataset = DocumentDataset(Path("data/train"))       # auto-discovers image+JSON/XML pairs
train, val, test = dataset.split(val_ratio=0.1, test_ratio=0.1)

gt = GroundTruthLoader.detect_and_load(Path("annotation.json"))  # or .xml
```

**RL training**
```python
from document_simulator.rl import RLTrainer, RLConfig

config = RLConfig(
    train_data_dir=Path("data/train"),
    num_envs=4,
    learning_rate=3e-4,
)
trainer = RLTrainer(config)
model = trainer.train(total_timesteps=1_000_000)
trainer.save(Path("models/best.zip"))
```

**Evaluation**
```python
from document_simulator.evaluation import Evaluator

ev = Evaluator(augmenter, ocr)
metrics = ev.evaluate_dataset(test_dataset)
# {"mean_original_cer": 0.04, "mean_augmented_cer": 0.12, "n_samples": 200, ...}
```

### CLI

```bash
# Augment a single image
uv run python -m document_simulator augment input.jpg output.jpg
uv run python -m document_simulator augment input.jpg output.jpg --pipeline heavy

# OCR
uv run python -m document_simulator ocr document.jpg
uv run python -m document_simulator ocr document.jpg --output result.txt --use-gpu

# Train RL agent
uv run python -m document_simulator train --data-dir ./data/train --num-steps 500000
uv run python -m document_simulator train --data-dir ./data/train --num-steps 500000 --output-dir ./models
```

---

## Configuration

Key settings in `.env` (copy from `.env.example`):

```bash
# Paths
DATA_DIR=./data
MODELS_DIR=./models
OUTPUT_DIR=./output

# OCR
PADDLEOCR_USE_GPU=false    # true for GPU
PADDLEOCR_LANG=en

# RL training
BATCH_SIZE=32
NUM_EPOCHS=100
LEARNING_RATE=0.001

# Optional experiment tracking
WANDB_PROJECT=document-simulator
LOG_LEVEL=INFO
```

---

## Development

```bash
# Tests
uv run pytest -m "not slow" -q          # fast tests only
uv run pytest -v                         # all tests, verbose
uv run pytest tests/unit/               # unit tests only
uv run pytest -k "test_augment"         # filter by name
uv run pytest --cov=document_simulator --cov-report=html

# Code quality
uv run black .
uv run ruff check . --fix
uv run mypy src/

# Git hooks
uv run pre-commit install
uv run pre-commit run --all-files
```

### GPU setup

```bash
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
# then set PADDLEOCR_USE_GPU=true in .env
uv run python -c "import torch; print(torch.cuda.is_available())"
```

### Troubleshooting

| Problem | Fix |
|---------|-----|
| Import errors after install | `rm -rf .venv && uv venv && uv sync` |
| CUDA not detected | Reinstall PyTorch with CUDA index URL above |
| PaddleOCR model download fails | Set `PADDLEOCR_DET_MODEL_DIR` / `PADDLEOCR_REC_MODEL_DIR` in `.env` |
| `augraphy_cache/` appearing in git status | Already in `.gitignore`; run `git status` to confirm |

---

## Performance targets

| Operation | CPU | GPU |
|-----------|-----|-----|
| Single image augmentation | ~100 ms | ~100 ms |
| OCR per page | ~500 ms | ~50 ms |
| RL training (1 M steps, 4 envs) | — | ~4–6 h |
| Batch throughput | >10 img/s | >50 img/s |

---

## Roadmap

- [ ] Pre-trained RL models for common document types
- [ ] `evaluate` CLI subcommand with ICDAR benchmark support
- [ ] Multi-page PDF ingestion
- [ ] Web UI for interactive augmentation preview
- [ ] Custom augmentation DSL
- [ ] Cloud deployment templates

---

## References

- [Augraphy](https://github.com/sparkfish/augraphy) — document image augmentation
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) — OCR engine
- [Stable-Baselines3](https://stable-baselines3.readthedocs.io/) — RL algorithms
- [Gymnasium](https://gymnasium.farama.org/) — RL environment API
- [uv](https://docs.astral.sh/uv/) — Python package manager

## License

MIT — see [LICENSE](LICENSE).
