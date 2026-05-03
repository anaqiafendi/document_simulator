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

# Install system libs needed by PyMuPDF, OpenCV, augraphy, WeasyPrint, and headless bpy.
#
# WeasyPrint (the `synthesis` extra, FDD #27 v0.1+) eagerly loads Pango via
# cffi at import time. Without these libs, `from weasyprint import HTML`
# crashes with `OSError: cannot load library 'pango-1.0-0'`, which takes
# down the FastAPI app at startup because the receipts package imports
# render at module load. Required: libpango-1.0-0 + libpangoft2-1.0-0
# + libharfbuzz0b + libcairo2.
#
# bpy 4.2 (the `synthesis-3d` extra, FDD #29 v0.3a) needs the full X11 +
# EGL + input + dbus stack even when running headless — these are eagerly
# loaded at `import bpy` time. The libxkbcommon0 + libdbus-1-3 additions
# came from CI failure on PR #30:
#   ImportError: libxkbcommon.so.0: cannot open shared object file
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libgl1 \
        libgomp1 \
        libsm6 \
        libxext6 \
        libxrender1 \
        libxi6 \
        libxxf86vm1 \
        libxfixes3 \
        libegl1 \
        libxkbcommon0 \
        libdbus-1-3 \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libharfbuzz0b \
        libcairo2 \
        libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy dependency manifests + README (hatchling needs README.md at build time)
COPY pyproject.toml uv.lock README.md ./

# Sync core deps + photoreal synthesis extras. ``synthesis`` brings in
# weasyprint/jinja2 for v0.1+v0.2; ``synthesis-3d`` brings in bpy 4.2 for the
# v0.3 3D scene + render path. Heavy ML extras (ocr, rl, ui) remain excluded.
RUN uv sync --no-dev --frozen --no-install-project --extra synthesis --extra synthesis-3d

# Copy source package
COPY src/ ./src/

# Install the project itself (no-deps, already synced above)
RUN uv sync --no-dev --frozen --extra synthesis --extra synthesis-3d

# Copy React build output.
# In HF Spaces, webapp/dist/ is gitignored so Docker can't access it directly.
# CI uploads the build artefact to webapp_dist/ (a non-gitignored path) so it
# is available in the Docker build context.
COPY webapp_dist/ ./webapp/dist/

# Copy sample data (optional — provides demo templates)
COPY data/ ./data/

# Enable OpenCV's OpenEXR codec — the v0.3 scene render decodes UV/depth
# passes from EXR via cv2; the codec is gated on this env var.
ENV OPENCV_IO_ENABLE_OPENEXR=1

# Expose FastAPI port
EXPOSE 7860

# Hugging Face Spaces uses port 7860 by default
# The React SPA is served by FastAPI StaticFiles from webapp/dist/
CMD ["/app/.venv/bin/uvicorn", "document_simulator.api.app:app", \
     "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
