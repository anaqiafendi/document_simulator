# Dockerfile — single Python stage
#
# The React SPA (webapp/dist/) is pre-built by CI (GitHub Actions) before
# being uploaded to the HF Space repo, so we don't need a Node build stage here.
# If you're building locally without a pre-built dist, run:
#   cd webapp && npm ci && npm run build
# first.

FROM python:3.11-slim

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
RUN uv sync --no-dev --frozen --no-install-project

# Copy source package
COPY src/ ./src/

# Install the project itself (no-deps, already synced above)
RUN uv sync --no-dev --frozen

# Copy pre-built React SPA from CI
COPY webapp/dist ./webapp/dist/

# Copy sample data (optional — provides demo templates)
COPY data/ ./data/

# Expose FastAPI port
EXPOSE 7860

CMD ["/app/.venv/bin/uvicorn", "document_simulator.api.app:app", \
     "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
