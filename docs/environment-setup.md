# Environment Setup - Document Simulator

## Overview

This document provides comprehensive instructions for setting up the Python environment for the Document Simulator project. The project uses `uv` for fast, reliable Python package management and virtual environment handling.

## Toolchain

- **Package manager:** uv (latest stable version)
- **Python version:** 3.11 (pinned via `.python-version`)
- **Virtual environment:** `.venv/` (managed by uv)
- **Build system:** hatchling (defined in `pyproject.toml`)

## Prerequisites

### System Requirements

- **Operating System:** macOS, Linux, or Windows
- **Python:** 3.10, 3.11, or 3.12 (3.11 recommended)
- **Memory:** Minimum 8GB RAM (16GB+ recommended for training)
- **Storage:** 10GB+ free space for models and data
- **Optional:** CUDA-capable GPU for accelerated training

### Install uv

```bash
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify installation
uv --version
```

## Quick Start

### Automated Setup (Recommended)

```bash
# Clone or navigate to the project
cd /path/to/document_simulator

# Run the setup script
chmod +x setup.sh
./setup.sh
```

The setup script will:
1. Install uv (if not present)
2. Pin Python version to 3.11
3. Create virtual environment at `.venv/`
4. Install all dependencies from `pyproject.toml`
5. Create necessary project directories
6. Generate `.env` file from template
7. Verify all imports work correctly

### Manual Setup

If you prefer manual control:

```bash
# 1. Pin Python version
uv python pin 3.11

# 2. Create virtual environment
uv venv

# 3. Install core dependencies
uv sync

# 4. Install optional dependency groups
uv sync --extra dev          # Development tools
uv sync --extra notebook     # Jupyter notebooks
uv sync --extra docs         # Documentation tools

# 5. Install all extras at once
uv sync --all-extras

# 6. Create project directories
mkdir -p data models output logs cache checkpoints

# 7. Create .env file
cp .env.example .env
```

## Dependency Groups

### Core Dependencies (Always Installed)

| Package | Purpose | Version |
|---------|---------|---------|
| `augraphy` | Document image augmentation | >=8.3.0 |
| `paddleocr` | OCR engine | >=2.7.0 |
| `paddlepaddle` | Deep learning framework for PaddleOCR | >=2.6.0 |
| `stable-baselines3` | Reinforcement learning algorithms | >=2.3.0 |
| `gymnasium` | RL environment interface | >=0.29.0 |
| `opencv-python` | Computer vision operations | >=4.9.0 |
| `torch` | PyTorch deep learning | >=2.2.0 |
| `numpy` | Numerical computing | >=1.26.0,<2.0.0 |
| `pillow` | Image handling | >=10.2.0 |
| `pydantic` | Data validation | >=2.6.0 |

### Optional: Development (`--extra dev`)

- `pytest`, `pytest-cov`, `pytest-asyncio` — Testing framework
- `black` — Code formatting
- `ruff` — Fast Python linter
- `mypy` — Static type checking
- `pre-commit` — Git hooks for code quality

### Optional: Notebooks (`--extra notebook`)

- `jupyter`, `jupyterlab` — Interactive notebooks
- `matplotlib`, `seaborn` — Data visualization

### Optional: Documentation (`--extra docs`)

- `mkdocs`, `mkdocs-material` — Documentation generation
- `mkdocstrings` — API documentation

## Using the Environment

### Activating Manually (Traditional)

```bash
# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

# Deactivate when done
deactivate
```

### Using uv run (Recommended)

No need to activate manually — `uv run` automatically uses the project's virtual environment:

```bash
# Run a Python script
uv run python src/document_simulator/main.py

# Run a module
uv run python -m document_simulator.cli

# Run pytest
uv run pytest

# Run with environment variables
uv run --env-file .env python train.py

# Install a new package
uv add requests

# Install a dev dependency
uv add --dev ipython
```

## Managing Dependencies

### Adding New Dependencies

```bash
# Add a runtime dependency
uv add <package_name>

# Add a development dependency
uv add --dev <package_name>

# Add a specific version
uv add "torch>=2.2.0,<3.0.0"

# Add multiple packages
uv add requests aiohttp httpx
```

After running `uv add`, the following happens automatically:
1. Package is added to `pyproject.toml`
2. `uv.lock` is regenerated with exact versions
3. Package is installed in `.venv/`

### Removing Dependencies

```bash
uv remove <package_name>
```

### Updating Dependencies

```bash
# Update all packages to latest compatible versions
uv sync --upgrade

# Update a specific package
uv add --upgrade <package_name>

# Check for outdated packages
uv pip list --outdated
```

### Viewing Installed Packages

```bash
# List all installed packages
uv pip list

# Show dependency tree
uv pip tree

# Show package details
uv pip show <package_name>
```

## Project Structure

```
document_simulator/
├── .venv/                      # Virtual environment (managed by uv)
├── src/
│   └── document_simulator/     # Main package
│       ├── __init__.py
│       ├── cli.py              # Command-line interface
│       ├── augmentation/       # Augraphy pipeline
│       ├── ocr/                # PaddleOCR integration
│       ├── rl/                 # Stable-Baselines3 training
│       ├── models/             # Model definitions
│       ├── data/               # Data loaders
│       └── utils/              # Helper functions
├── tests/                      # Test suite
├── notebooks/                  # Jupyter notebooks
├── data/                       # Datasets (gitignored)
├── models/                     # Trained models (gitignored)
├── output/                     # Generated outputs (gitignored)
├── logs/                       # Training logs (gitignored)
├── cache/                      # Cache directory (gitignored)
├── checkpoints/                # Model checkpoints (gitignored)
├── docs/                       # Documentation
│   └── environment-setup.md    # This file
├── pyproject.toml              # Project metadata and dependencies
├── uv.lock                     # Exact dependency versions
├── .python-version             # Python version pin (3.11)
├── .env.example                # Environment variable template
├── .env                        # Local environment config (gitignored)
├── .gitignore                  # Git ignore rules
├── setup.sh                    # Automated setup script
└── README.md                   # Project overview
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Key configuration options:

```bash
# Project paths
DATA_DIR=./data
MODELS_DIR=./models
OUTPUT_DIR=./output

# PaddleOCR settings
PADDLEOCR_USE_GPU=false        # Set to 'true' if you have CUDA GPU
PADDLEOCR_LANG=en              # OCR language (en, ch, etc.)

# Training settings
BATCH_SIZE=32
NUM_EPOCHS=100
LEARNING_RATE=0.001
RANDOM_SEED=42

# Logging
LOG_LEVEL=INFO
WANDB_PROJECT=document-simulator  # Optional: Weights & Biases
```

### Python Version Management

The project pins Python 3.11 via `.python-version`. To change:

```bash
# Pin a different version
uv python pin 3.10

# uv will automatically download and use the specified version
uv sync
```

## Troubleshooting

### Issue: `uv` command not found

**Solution:**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH (add to ~/.bashrc or ~/.zshrc for persistence)
export PATH="$HOME/.cargo/bin:$PATH"
```

### Issue: Import errors after installation

**Solution:**
```bash
# Ensure you're using the venv
uv run python -c "import sys; print(sys.executable)"

# Reinstall dependencies
rm -rf .venv uv.lock
uv venv
uv sync
```

### Issue: CUDA / GPU not detected

**Solution:**
```bash
# Install PyTorch with CUDA support (example for CUDA 11.8)
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Verify CUDA availability
uv run python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### Issue: PaddleOCR model download fails

**Solution:**
```bash
# Manually specify model directories in .env
PADDLEOCR_DET_MODEL_DIR=./models/paddle/det
PADDLEOCR_REC_MODEL_DIR=./models/paddle/rec

# Or download models manually from:
# https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.7/doc/doc_en/models_list_en.md
```

### Issue: Memory errors during training

**Solution:**
```bash
# Reduce batch size in .env
BATCH_SIZE=16  # or 8

# Reduce number of workers
NUM_WORKERS=2

# Enable gradient checkpointing (in training script)
```

### Issue: `uv.lock` conflicts after git merge

**Solution:**
```bash
# Regenerate lockfile from pyproject.toml
rm uv.lock
uv sync
```

## Dependency Manifest

All dependencies are declared in `pyproject.toml` under:
- `[project.dependencies]` — Core runtime dependencies
- `[project.optional-dependencies]` — Optional feature groups (dev, docs, notebook)
- `[tool.uv.dev-dependencies]` — uv-specific dev dependencies

The `uv.lock` file pins exact versions for reproducibility. **Do not edit `uv.lock` manually** — it is auto-generated by `uv sync` and `uv add`.

## Testing the Environment

### Verify All Imports

```bash
uv run python -c "
import augraphy
import paddleocr
import stable_baselines3
import cv2
import torch
import numpy as np
print('✅ All core packages imported successfully')
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
"
```

### Run Tests

```bash
# Install dev dependencies first
uv sync --extra dev

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=document_simulator --cov-report=html
```

### Check Code Quality

```bash
# Format code
uv run black .

# Lint code
uv run ruff check .

# Type check
uv run mypy src/
```

## Performance Optimization

### Use GPU Acceleration (if available)

1. Install CUDA-enabled PyTorch:
```bash
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

2. Update `.env`:
```bash
PADDLEOCR_USE_GPU=true
```

3. Verify:
```bash
uv run python -c "import torch; print(torch.cuda.is_available())"
```

### Optimize Data Loading

Adjust in `.env`:
```bash
NUM_WORKERS=8              # Number of parallel data loading workers
PREFETCH_FACTOR=4          # Number of batches to prefetch
PIN_MEMORY=true            # Faster GPU transfer
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Set up Python
        run: uv python pin 3.11
      - name: Install dependencies
        run: uv sync --all-extras
      - name: Run tests
        run: uv run pytest
```

## References

### Official Documentation
- **uv**: https://docs.astral.sh/uv/
- **Augraphy**: https://github.com/sparkfish/augraphy
- **PaddleOCR**: https://github.com/PaddlePaddle/PaddleOCR
- **Stable-Baselines3**: https://stable-baselines3.readthedocs.io/
- **PyTorch**: https://pytorch.org/docs/stable/index.html

### uv Guides
- Environments: https://docs.astral.sh/uv/pip/environments/
- Packages: https://docs.astral.sh/uv/pip/packages/
- Projects: https://realpython.com/python-uv/#handling-python-projects-with-uv

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section above
2. Review `RESEARCH_FINDINGS.md` for project-specific details
3. Open an issue on the project repository
4. Consult the official documentation links above

---

**Last Updated:** 2024-03-01
**Maintained by:** Document Simulator Team
