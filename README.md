# Document Simulator

> **Document image augmentation and OCR training system** using Augraphy, PaddleOCR, and Stable-Baselines3

## Overview

Document Simulator is a Python-based system for:
- **Document Image Augmentation**: Realistic degradation and augmentation using Augraphy
- **OCR Training**: Train and fine-tune OCR models with PaddleOCR
- **Reinforcement Learning**: Optimize document processing pipelines with Stable-Baselines3

## Features

- Document augmentation with 100+ realistic transformations
- End-to-end OCR pipeline with detection and recognition
- RL-based pipeline optimization for document quality enhancement
- Support for multiple document types (receipts, forms, handwritten, printed)
- Extensible architecture for custom augmentation strategies
- GPU acceleration support
- Experiment tracking with TensorBoard and Weights & Biases

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/document-simulator.git
cd document-simulator

# Run automated setup (installs uv, creates venv, installs dependencies)
chmod +x setup.sh
./setup.sh
```

### Usage

```bash
# Activate the virtual environment
source .venv/bin/activate

# Or use uv run (no activation needed)
uv run python -m document_simulator --help
```

## Getting Started

This project uses [uv](https://docs.astral.sh/uv/) for Python environment and dependency management.

### Prerequisites

- Python 3.10, 3.11, or 3.12 (3.11 recommended)
- 8GB+ RAM (16GB+ recommended for training)
- Optional: CUDA-capable GPU for accelerated training

### Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Set up the environment
uv venv && uv sync

# Install optional extras
uv sync --extra dev          # Development tools (pytest, black, mypy)
uv sync --extra notebook     # Jupyter notebooks
uv sync --all-extras         # Install everything

# Create project directories
mkdir -p data models output logs cache checkpoints

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

See [`docs/environment-setup.md`](docs/environment-setup.md) for detailed setup instructions and troubleshooting.

## Project Structure

```
document_simulator/
├── src/
│   └── document_simulator/     # Main package
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
├── docs/                       # Documentation
├── pyproject.toml              # Project metadata and dependencies
└── README.md                   # This file
```

## Core Dependencies

| Package | Purpose |
|---------|---------|
| [Augraphy](https://github.com/sparkfish/augraphy) | Document image augmentation with 100+ realistic transformations |
| [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) | State-of-the-art OCR for detection and recognition |
| [Stable-Baselines3](https://stable-baselines3.readthedocs.io/) | Reinforcement learning for pipeline optimization |
| [PyTorch](https://pytorch.org/) | Deep learning framework |
| [OpenCV](https://opencv.org/) | Computer vision operations |

See `pyproject.toml` for the complete dependency list.

## Usage Examples

### Document Augmentation

```python
from document_simulator.augmentation import DocumentAugmenter

# Initialize augmenter with Augraphy pipeline
augmenter = DocumentAugmenter()

# Apply augmentation to an image
augmented_image = augmenter.augment('path/to/document.jpg')
```

### OCR Processing

```python
from document_simulator.ocr import OCREngine

# Initialize PaddleOCR engine
ocr = OCREngine(use_gpu=True)

# Extract text from document
result = ocr.recognize('path/to/document.jpg')
print(result['text'])
```

### RL Pipeline Optimization

```python
from document_simulator.rl import PipelineOptimizer

# Train RL agent to optimize augmentation parameters
optimizer = PipelineOptimizer()
optimizer.train(num_steps=100000)

# Use trained agent to process documents
optimized_image = optimizer.process('path/to/document.jpg')
```

## Configuration

Key settings in `.env`:

```bash
# Data paths
DATA_DIR=./data
MODELS_DIR=./models
OUTPUT_DIR=./output

# PaddleOCR
PADDLEOCR_USE_GPU=false    # Set to 'true' for GPU acceleration
PADDLEOCR_LANG=en          # OCR language

# Training
BATCH_SIZE=32
NUM_EPOCHS=100
LEARNING_RATE=0.001

# Logging
LOG_LEVEL=INFO
WANDB_PROJECT=document-simulator  # Optional
```

## Development

### Running Tests

```bash
# Install dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=document_simulator --cov-report=html
```

### Code Quality

```bash
# Format code
uv run black .

# Lint code
uv run ruff check .

# Type check
uv run mypy src/
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run hooks manually
uv run pre-commit run --all-files
```

## GPU Support

For GPU acceleration:

```bash
# Install PyTorch with CUDA (example for CUDA 11.8)
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Update .env
PADDLEOCR_USE_GPU=true

# Verify
uv run python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

## Documentation

- [Environment Setup Guide](docs/environment-setup.md) — Detailed installation and configuration
- [RESEARCH_FINDINGS.md](RESEARCH_FINDINGS.md) — Research background and design decisions
- [API Documentation](docs/api/) — Generated API docs

## Troubleshooting

### Common Issues

**Import errors after installation:**
```bash
rm -rf .venv uv.lock
uv venv && uv sync
```

**CUDA not detected:**
```bash
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

**PaddleOCR model download fails:**
```bash
# Manually specify model directories in .env
PADDLEOCR_DET_MODEL_DIR=./models/paddle/det
PADDLEOCR_REC_MODEL_DIR=./models/paddle/rec
```

See [Environment Setup — Troubleshooting](docs/environment-setup.md#troubleshooting) for more solutions.

## Architecture

### Augmentation Pipeline (Augraphy)

```
Input Image → Ink → Paper → Post → Output Image
```

Augraphy provides 100+ transformations including:
- Ink degradation (fading, bleeding, erosion)
- Paper effects (noise, wrinkles, watermarks)
- Post-processing (blur, contrast, brightness)

### OCR Pipeline (PaddleOCR)

```
Image → Text Detection → Text Recognition → Structured Output
```

PaddleOCR supports:
- Multi-language OCR (80+ languages)
- Scene text detection
- Document layout analysis
- Table recognition

### RL Optimization (Stable-Baselines3)

```
Environment (Document State) → Agent (PPO/DQN) → Action (Augmentation Params) → Reward (OCR Quality)
```

RL agent learns to:
- Select optimal augmentation parameters
- Balance realism vs. OCR accuracy
- Adapt to different document types

## Performance

Typical performance on a modern CPU:
- Document augmentation: ~100ms per image
- OCR processing: ~500ms per page (CPU), ~50ms per page (GPU)
- RL training: ~1M steps in 4-6 hours (GPU)

## Roadmap

- [ ] Pre-trained models for common document types
- [ ] Web UI for interactive augmentation
- [ ] Multi-page PDF support
- [ ] Document layout analysis integration
- [ ] Custom augmentation DSL
- [ ] Cloud deployment templates

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Ensure all tests pass and code is formatted:
```bash
uv run pytest
uv run black .
uv run ruff check .
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## References

- **Augraphy**: https://github.com/sparkfish/augraphy
- **PaddleOCR**: https://github.com/PaddlePaddle/PaddleOCR
- **Stable-Baselines3**: https://stable-baselines3.readthedocs.io/
- **uv**: https://docs.astral.sh/uv/
- **PyTorch**: https://pytorch.org/

## Citation

If you use this project in your research, please cite:

```bibtex
@software{document_simulator,
  title = {Document Simulator: Document Image Augmentation and OCR Training},
  author = {Your Name},
  year = {2024},
  url = {https://github.com/yourusername/document-simulator}
}
```

## Support

- Open an issue for bug reports or feature requests
- See [docs/environment-setup.md](docs/environment-setup.md) for setup help
- Consult [RESEARCH_FINDINGS.md](RESEARCH_FINDINGS.md) for project background

---

**Built with** ❤️ **using Augraphy, PaddleOCR, and Stable-Baselines3**
