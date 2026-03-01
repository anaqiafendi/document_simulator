#!/bin/bash
set -e

# Document Simulator - Environment Setup Script
# This script sets up the Python environment using uv

echo "🚀 Document Simulator - Environment Setup"
echo "=========================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if uv is installed
echo "Checking for uv..."
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}⚠️  uv not found. Installing uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Add uv to PATH for this session
    export PATH="$HOME/.cargo/bin:$PATH"

    # Verify installation
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}❌ Failed to install uv. Please install manually: https://docs.astral.sh/uv/${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ uv installed successfully${NC}"
else
    echo -e "${GREEN}✅ uv is already installed ($(uv --version))${NC}"
fi

echo ""
echo "Checking Python version..."
python3 --version

# Pin Python version
echo ""
echo "Pinning Python version to 3.11..."
uv python pin 3.11

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment already exists. Skipping creation.${NC}"
else
    uv venv
    echo -e "${GREEN}✅ Virtual environment created at .venv/${NC}"
fi

# Sync dependencies
echo ""
echo "Installing dependencies from pyproject.toml..."
uv sync

echo ""
echo -e "${GREEN}✅ Core dependencies installed${NC}"

# Install dev dependencies
echo ""
read -p "Install development dependencies? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing development dependencies..."
    uv sync --extra dev
    echo -e "${GREEN}✅ Development dependencies installed${NC}"
fi

# Install notebook dependencies
echo ""
read -p "Install Jupyter notebook dependencies? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing notebook dependencies..."
    uv sync --extra notebook
    echo -e "${GREEN}✅ Notebook dependencies installed${NC}"
fi

# Create necessary directories
echo ""
echo "Creating project directories..."
mkdir -p data models output logs cache checkpoints
touch data/.gitkeep models/.gitkeep output/.gitkeep logs/.gitkeep cache/.gitkeep checkpoints/.gitkeep
echo -e "${GREEN}✅ Project directories created${NC}"

# Copy environment template
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo -e "${GREEN}✅ .env file created. Please update with your settings.${NC}"
else
    echo -e "${YELLOW}⚠️  .env file already exists. Skipping.${NC}"
fi

# Verify installation
echo ""
echo "Verifying installation..."
uv run python -c "
import sys
print(f'Python version: {sys.version}')
print(f'Python executable: {sys.executable}')
print()
print('Testing imports...')
try:
    import augraphy
    print('✅ Augraphy imported successfully')
except ImportError as e:
    print(f'❌ Augraphy import failed: {e}')

try:
    import paddleocr
    print('✅ PaddleOCR imported successfully')
except ImportError as e:
    print(f'❌ PaddleOCR import failed: {e}')

try:
    import stable_baselines3
    print('✅ Stable-Baselines3 imported successfully')
except ImportError as e:
    print(f'❌ Stable-Baselines3 import failed: {e}')

try:
    import cv2
    print('✅ OpenCV imported successfully')
except ImportError as e:
    print(f'❌ OpenCV import failed: {e}')

try:
    import torch
    print('✅ PyTorch imported successfully')
except ImportError as e:
    print(f'❌ PyTorch import failed: {e}')
"

echo ""
echo -e "${GREEN}=========================================="
echo "✅ Setup complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source .venv/bin/activate"
echo ""
echo "2. Or run commands with uv:"
echo "   uv run python your_script.py"
echo ""
echo "3. Update .env with your configuration"
echo ""
echo "4. See docs/environment-setup.md for detailed documentation"
echo ""
