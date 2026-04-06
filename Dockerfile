# Multi-stage Dockerfile
# Stage 1: build the React SPA
# Stage 2: Python + FastAPI serves everything

# ─── Stage 1: Node build ────────────────────────────────────────────────────
FROM node:20-slim AS node-builder

WORKDIR /build/webapp
COPY webapp/package*.json ./
RUN npm ci --ignore-scripts

COPY webapp/ .
RUN npm run build
# Output: /build/webapp/dist/

# ─── Stage 2: Python runtime ─────────────────────────────────────────────────
FROM python:3.11-slim AS python-app

# Install system libs needed by PyMuPDF, OpenCV, and augraphy
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libgl1 \
        libgomp1 \
        libsm6 \
        libxext6 \
        libxrender1 \
        libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy dependency manifests + README (hatchling needs README.md at build time)
COPY pyproject.toml uv.lock README.md ./

# Sync core deps only — heavy optional extras (ocr, rl, ui) are excluded.
# Core = augraphy + fastapi + synthesis. Image is ~800 MB.
RUN uv sync --no-dev --frozen --no-install-project

# Copy source package
COPY src/ ./src/

# Install the project itself (no-deps, already synced above)
RUN uv sync --no-dev --frozen

# Copy React build output from stage 1
COPY --from=node-builder /build/webapp/dist ./webapp/dist/

# Copy sample data (optional — provides demo templates)
COPY data/ ./data/

# Expose FastAPI port
EXPOSE 7860

# Hugging Face Spaces uses port 7860 by default
# The React SPA is served by FastAPI StaticFiles from webapp/dist/
CMD ["/app/.venv/bin/uvicorn", "document_simulator.api.app:app", \
     "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
