# Single-stage Dockerfile for HF Spaces deployment.
#
# The React SPA is pre-built by the CI workflow (preview-deploy.yml /
# deploy-hf.yml) on a standard Ubuntu runner where esbuild works normally.
# The built webapp/dist/ is uploaded to the HF Space before Docker runs, so
# the image just copies the artefact — no Node.js stage needed.
#
# For local Docker builds, run `cd webapp && npm ci && npm run build` first
# so that webapp/dist/ exists in the build context.

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

# Copy React build output.
# In HF Spaces, webapp/dist/ is gitignored so Docker can't access it directly.
# CI uploads the build artefact to webapp_dist/ (a non-gitignored path) so it
# is available in the Docker build context.
COPY webapp_dist/ ./webapp/dist/

# Copy sample data (optional — provides demo templates)
COPY data/ ./data/

# Expose FastAPI port
EXPOSE 7860

# Hugging Face Spaces uses port 7860 by default
# The React SPA is served by FastAPI StaticFiles from webapp/dist/
CMD ["/app/.venv/bin/uvicorn", "document_simulator.api.app:app", \
     "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
