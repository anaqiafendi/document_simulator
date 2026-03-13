"""FastAPI application factory for Document Simulator API."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from document_simulator.api.routers import synthesis
from document_simulator.api.routers import augmentation as augmentation_router
from document_simulator.api.routers import ocr as ocr_router
from document_simulator.api.routers import batch as batch_router
from document_simulator.api.routers import evaluation as evaluation_router
from document_simulator.api.routers import rl_training as rl_training_router

app = FastAPI(title="Document Simulator API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:7860"],  # Vite dev + Docker
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(synthesis.router)
app.include_router(augmentation_router.router)
app.include_router(ocr_router.router)
app.include_router(batch_router.router)
app.include_router(evaluation_router.router)
app.include_router(rl_training_router.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}


# Mount the React SPA if it has been built (conditional — dev-friendly)
# Uses a catch-all to support React Router client-side navigation.
DIST_DIR = Path(__file__).resolve().parents[3] / "webapp" / "dist"

if DIST_DIR.is_dir():
    from fastapi.staticfiles import StaticFiles

    # Mount static assets (JS, CSS, images) at /assets
    assets_dir = DIST_DIR / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # Catch-all: serve index.html for all non-API routes so React Router works
    @app.get("/{full_path:path}")
    def serve_spa(full_path: str) -> FileResponse:
        """Serve the React SPA for all non-API routes."""
        index = DIST_DIR / "index.html"
        return FileResponse(str(index))
