# Setup Instructions - Document Simulator

Quick reference guide for setting up the Document Simulator environment.

## Prerequisites

- Python 3.10, 3.11, or 3.12 installed (3.11 recommended)
- 8GB+ RAM (16GB+ recommended for training)
- 10GB+ free disk space
- Optional: CUDA-capable GPU for acceleration

---

## Quick Start (Automated)

```bash
# Navigate to project directory
cd /Users/amuhamadafendi/Git_VSCode/document_simulator

# Make setup script executable
chmod +x setup.sh

# Run automated setup
./setup.sh
```

The script will:
1. Install `uv` if not present
2. Pin Python 3.11
3. Create virtual environment
4. Install all dependencies
5. Create project directories
6. Generate `.env` file
7. Verify installation

**Setup time:** 3-8 minutes

---

## Manual Setup (Step-by-Step)

### 1. Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify
uv --version
```

### 2. Create Virtual Environment

```bash
# Pin Python version
uv python pin 3.11

# Create venv
uv venv

# Verify venv created
ls -la .venv/
```

### 3. Install Dependencies

```bash
# Install core dependencies
uv sync

# Install dev tools (pytest, black, ruff, mypy)
uv sync --extra dev

# Install Jupyter notebooks
uv sync --extra notebook

# Install everything
uv sync --all-extras
```

### 4. Create Project Directories

```bash
mkdir -p data models output logs cache checkpoints
touch data/.gitkeep models/.gitkeep output/.gitkeep logs/.gitkeep cache/.gitkeep checkpoints/.gitkeep
```

### 5. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit with your settings
nano .env  # or vim, code, etc.
```

### 6. Verify Installation

```bash
# Test imports
uv run python -c "
import augraphy
import paddleocr
import stable_baselines3
import cv2
import torch
print('✅ All packages imported successfully')
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
"
```

---

## GPU Setup (Optional)

For CUDA acceleration:

```bash
# Check CUDA version
nvidia-smi

# Install PyTorch with CUDA 11.8
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Or CUDA 12.1
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Update .env
echo "PADDLEOCR_USE_GPU=true" >> .env

# Verify GPU
uv run python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, Devices: {torch.cuda.device_count()}')"
```

---

## Running the Project

### Activate Environment (Traditional)

```bash
# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

# When done
deactivate
```

### Using uv run (Recommended)

No activation needed:

```bash
# Run Python scripts
uv run python script.py

# Run CLI commands
uv run python -m document_simulator --help

# Run tests
uv run pytest
```

---

## Basic Usage Examples

### 1. Document Augmentation

```bash
# Augment a single image
uv run python -m document_simulator augment input.jpg output.jpg

# With custom pipeline
uv run python -m document_simulator augment input.jpg output.jpg --pipeline heavy
```

### 2. OCR Processing

```bash
# Extract text from image
uv run python -m document_simulator ocr input.jpg

# Save to file
uv run python -m document_simulator ocr input.jpg --output result.txt

# Use GPU
uv run python -m document_simulator ocr input.jpg --use-gpu
```

### 3. RL Training

```bash
# Train pipeline optimizer
uv run python -m document_simulator train --data-dir ./data --num-steps 100000
```

---

## Development Workflow

### Install Development Tools

```bash
uv sync --extra dev
```

### Run Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=document_simulator --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Code Formatting

```bash
# Format code
uv run black .

# Check formatting (dry run)
uv run black --check .
```

### Linting

```bash
# Lint code
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .
```

### Type Checking

```bash
# Check types
uv run mypy src/
```

### Pre-commit Hooks

```bash
# Install hooks
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files
```

---

## Common Tasks

### Add a New Dependency

```bash
# Runtime dependency
uv add requests

# Dev dependency
uv add --dev ipython

# Specific version
uv add "numpy>=1.26.0,<2.0.0"
```

### Update Dependencies

```bash
# Update all
uv sync --upgrade

# Update specific package
uv add --upgrade torch
```

### Remove a Dependency

```bash
uv remove package_name
```

### View Installed Packages

```bash
# List all
uv pip list

# Show dependency tree
uv pip tree

# Check for outdated
uv pip list --outdated
```

---

## Troubleshooting

### Issue: `uv` not found

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH
export PATH="$HOME/.cargo/bin:$PATH"

# Make permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Issue: Import errors

```bash
# Rebuild environment
rm -rf .venv uv.lock
uv venv
uv sync
```

### Issue: CUDA not detected

```bash
# Verify CUDA installation
nvidia-smi

# Reinstall PyTorch with CUDA
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Test
uv run python -c "import torch; print(torch.cuda.is_available())"
```

### Issue: PaddleOCR model download fails

```bash
# Set model directories in .env
export PADDLEOCR_DET_MODEL_DIR=./models/paddle/det
export PADDLEOCR_REC_MODEL_DIR=./models/paddle/rec

# Or download manually from:
# https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.7/doc/doc_en/models_list_en.md
```

### Issue: Memory errors during training

```bash
# Reduce batch size in .env
echo "BATCH_SIZE=16" >> .env

# Reduce workers
echo "NUM_WORKERS=2" >> .env
```

### Issue: Permission denied on setup.sh

```bash
chmod +x setup.sh
./setup.sh
```

---

## Project Structure Reference

```
document_simulator/
├── .venv/                  # Virtual environment (created by setup)
├── src/
│   └── document_simulator/
│       ├── augmentation/   # Augraphy pipelines
│       ├── ocr/            # PaddleOCR integration
│       ├── rl/             # Stable-Baselines3 training
│       └── utils/          # Helper functions
├── tests/                  # Test suite
├── docs/                   # Documentation
├── data/                   # Datasets (create on setup)
├── models/                 # Trained models (create on setup)
├── output/                 # Outputs (create on setup)
├── logs/                   # Logs (create on setup)
├── pyproject.toml          # Dependencies & config
├── .env                    # Local config (create from .env.example)
└── setup.sh                # Setup script
```

---

## Environment Variables (.env)

Key settings to configure:

```bash
# Paths
DATA_DIR=./data
MODELS_DIR=./models
OUTPUT_DIR=./output

# PaddleOCR
PADDLEOCR_USE_GPU=false     # Set to 'true' for GPU
PADDLEOCR_LANG=en           # OCR language

# Training
BATCH_SIZE=32
NUM_EPOCHS=100
LEARNING_RATE=0.001

# Logging
LOG_LEVEL=INFO
WANDB_PROJECT=document-simulator  # Optional
```

---

## Next Steps

1. ✅ Complete setup using `./setup.sh` or manual steps
2. ✅ Verify installation with test imports
3. ✅ Configure `.env` with your settings
4. ✅ Run tests: `uv run pytest`
5. ✅ Review documentation in `docs/environment-setup.md`
6. ✅ Check research findings in `RESEARCH_FINDINGS.md`
7. ✅ Start developing!

---

## Additional Resources

- **Detailed Setup Guide:** [`docs/environment-setup.md`](docs/environment-setup.md)
- **Project Overview:** [`README.md`](README.md)
- **Research & Architecture:** [`RESEARCH_FINDINGS.md`](RESEARCH_FINDINGS.md)
- **Audit Report:** [`ENVIRONMENT_AUDIT_REPORT.md`](ENVIRONMENT_AUDIT_REPORT.md)

- **uv Documentation:** https://docs.astral.sh/uv/
- **Augraphy:** https://github.com/sparkfish/augraphy
- **PaddleOCR:** https://github.com/PaddlePaddle/PaddleOCR
- **Stable-Baselines3:** https://stable-baselines3.readthedocs.io/

---

**For questions or issues, see the troubleshooting section above or consult the full documentation.**

**Status:** ✅ Ready for Development
