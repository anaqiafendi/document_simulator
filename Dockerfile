FROM python:3.11-slim

# System dependencies required by OpenCV, PaddleOCR, and other native libs
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libgl1 \
       libsm6 \
       libxext6 \
       libxrender-dev \
       git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ── Layer 1: install all third-party deps (cached independently of app code) ──
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# ── Layer 2: install app source ────────────────────────────────────────────────
COPY src/ ./src/
RUN uv sync --frozen --no-dev

# Copy static assets and Streamlit config
COPY data/ ./data/
COPY .streamlit/ ./.streamlit/

ENV PATH="/app/.venv/bin:$PATH"

# HF Spaces requires port 7860
EXPOSE 7860

CMD ["streamlit", "run", "src/document_simulator/ui/app.py", \
     "--server.port=7860", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
