"""FastAPI application factory for Document Simulator API."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from document_simulator.api.routers import synthesis

app = FastAPI(title="Document Simulator API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(synthesis.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}


# Mount the React SPA if it has been built (conditional — dev-friendly)
DIST_DIR = Path(__file__).resolve().parents[3] / "webapp" / "dist"

if DIST_DIR.is_dir():
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=str(DIST_DIR), html=True), name="static")
