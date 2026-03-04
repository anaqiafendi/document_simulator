# Feature: Hugging Face Spaces Deployment

> **GitHub Issue:** `#hosting`
> **Status:** `complete`
> **Module:** `deployment`

---

## Summary

Package the Document Simulator Streamlit app as a Docker image deployable to Hugging
Face Spaces, providing a fast, free, always-available alternative to Streamlit Community
Cloud.

---

## Motivation

### Problem Statement

Streamlit Community Cloud is extremely slow for this app: heavy dependencies (torch,
paddleocr, augraphy, opencv) cause cold starts exceeding 5 minutes and the 1 GB RAM
ceiling causes OOM errors under normal use. The app is essentially unusable when hosted
there.

### Value Delivered

- The full app runs for free on HF Spaces' CPU tier (2 vCPU / 16 GB RAM).
- Docker-based deployment gives reproducible builds and a single source of truth for
  the runtime environment.
- Layer-cached `uv sync` makes rebuilds fast after dependency changes.
- Any contributor can deploy their own Space in under 10 minutes.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| Developer | I can push to GitHub and have the Space auto-update | Changes are live without manual intervention |
| User | I can open the app and have it load in under 60 seconds | I can actually use it |
| Contributor | I can fork and deploy my own Space for testing | I can demo changes before merging |

---

## Acceptance Criteria

- [ ] AC-1: `Dockerfile` builds successfully with `docker build .`
- [ ] AC-2: Container starts and Streamlit serves on port 7860
- [ ] AC-3: `docker run` exposes the home page at `http://localhost:7860`
- [ ] AC-4: All 5 app pages load without import errors
- [ ] AC-5: `.streamlit/config.toml` disables CORS/XSRF (required for HF Spaces embedding)
- [ ] AC-6: `.dockerignore` excludes `.venv`, `cache/`, `logs/`, `output/`, `models/` so
  the build context stays under 50 MB
- [ ] AC-7: `tests/test_deployment.py` passes, validating Dockerfile and config content

---

## Design

### Public API

This is an infrastructure feature — no Python API. The user-facing surface is:

```bash
# Build locally
docker build -t document-simulator .

# Run locally (mirrors HF Spaces environment)
docker run -p 7860:7860 document-simulator

# Open in browser
open http://localhost:7860
```

```bash
# Deploy to HF Spaces (one-time setup)
# 1. Create a Space at https://huggingface.co/new-space (Docker SDK, public)
# 2. Add the HF remote
git remote add space https://huggingface.co/spaces/<username>/document-simulator
# 3. Push
git push space feature/hosting-research:main
```

### Data Flow

```
GitHub repo (pyproject.toml + uv.lock + src/)
    │
    ▼
docker build (multi-stage uv install)
    │  Layer 1: python:3.11-slim + apt packages (libgl1 …)
    │  Layer 2: uv binary
    │  Layer 3: Python deps from uv.lock  ← heavy, cached
    │  Layer 4: app source (src/, data/, .streamlit/)
    ▼
Docker image (~4–6 GB)
    │
    ▼
HF Spaces container runtime
    │  port 7860, 2 vCPU, 16 GB RAM
    ▼
Streamlit app (http://<space-url>)
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `Dockerfile` | config | Full image definition; uv-based dep install |
| `.dockerignore` | config | Keeps build context small |
| `.streamlit/config.toml` | config | Disables CORS/XSRF, sets headless mode |

### Configuration

HF Spaces requires port **7860** (not Streamlit's default 8501). This is set in the
`Dockerfile` `CMD` and `EXPOSE` directive — no `.env` change is needed.

| Setting | Location | Value | Reason |
|---------|----------|-------|--------|
| `server.port` | `CMD` in Dockerfile | `7860` | HF Spaces requirement |
| `server.address` | `CMD` in Dockerfile | `0.0.0.0` | Bind to all interfaces |
| `server.headless` | `.streamlit/config.toml` | `true` | Suppress browser-open attempt |
| `server.enableCORS` | `.streamlit/config.toml` | `false` | Required for HF iframe embedding |
| `server.enableXsrfProtection` | `.streamlit/config.toml` | `false` | Required for HF iframe embedding |

---

## Implementation

### Files

| Path | Role |
|------|------|
| `Dockerfile` | Image definition; installs system deps + Python deps via uv |
| `.dockerignore` | Excludes venv, cache, logs, models from build context |
| `.streamlit/config.toml` | Streamlit server settings for containerised deployment |
| `tests/test_deployment.py` | Validates Dockerfile and config are correctly formed |

### Key Architectural Decisions

1. **Single-stage Docker build (not multi-stage)** — A multi-stage build would produce
   a smaller final image by discarding the uv binary and build cache, but it
   complicates the layer structure and the size saving is minimal since the Python
   packages (not the uv binary) dominate the image size. A clean single-stage build is
   easier to read and debug.

2. **`uv sync --frozen --no-dev`** — `--frozen` ensures the exact `uv.lock` is used
   (no implicit re-resolution on Streamlit Cloud or HF Spaces). `--no-dev` omits
   pytest/black/mypy, saving ~50 MB and keeping the prod image clean.

3. **`--no-install-project` on first `uv sync`** — The first sync (before copying
   `src/`) installs all third-party dependencies without the local package. This allows
   Docker to cache the expensive dependency layer independently from app source changes,
   so a code-only change doesn't re-install 270 packages.

4. **Port 7860** — HF Spaces proxies port 7860 exclusively. Any other port simply won't
   be reachable. This differs from the Streamlit Community Cloud convention of 8501.

5. **`libgl1` and related system packages in `packages.txt` and `Dockerfile`** — OpenCV
   requires `libGL.so.1`. We install it in the Dockerfile's apt layer. The repo-level
   `packages.txt` covers Streamlit Community Cloud if that's ever used again.

### Known Edge Cases & Constraints

- **Sleep after 30 min idle** — HF Spaces free tier pauses the container. Wake time is
  30–120 seconds. This is unavoidable on the free tier; upgrade to a paid hardware
  tier to eliminate it.
- **Ephemeral filesystem** — Files written inside the container (uploaded docs, OCR
  outputs) are lost on restart/sleep. For persistent storage, add an HF Dataset as a
  mounted volume or use HF persistent storage (paid).
- **PaddleOCR model downloads** — PaddleOCR downloads models to `~/.paddleocr` on first
  run if they're not on disk. These are re-downloaded after every sleep-induced restart.
  Future work: bake models into the image.
- **Background threads** — `05_rl_training.py` uses `threading.Thread`. These survive
  Streamlit reruns within a session but die if the container restarts.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/test_deployment.py` | unit | 7 | Dockerfile structure, config content, dockerignore |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_dockerfile_exists` | `tests/test_deployment.py` | `FileNotFoundError` |
| `test_dockerfile_exposes_7860` | `tests/test_deployment.py` | `AssertionError: EXPOSE 7860 not found` |
| `test_streamlit_config_exists` | `tests/test_deployment.py` | `FileNotFoundError` |
| `test_streamlit_config_disables_cors` | `tests/test_deployment.py` | `AssertionError` |
| `test_dockerignore_excludes_venv` | `tests/test_deployment.py` | `FileNotFoundError` |

**Green — minimal implementation:**

Create `Dockerfile`, `.streamlit/config.toml`, `.dockerignore` with the minimum content
to pass the assertions.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Added `--no-install-project` to first `uv sync` | Enables Docker layer caching for deps |
| Added full apt package list (libsm6, libxext6, libxrender-dev) | PaddleOCR needs these on Debian slim |

### How to Run

```bash
# All deployment tests
uv run pytest tests/test_deployment.py -v --no-cov

# With coverage
uv run pytest tests/test_deployment.py --cov=document_simulator
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `docker` (CLI) | external tool | Building and running the image locally |
| `uv` | external tool | Installed into Docker image for dep management |
| `libgl1` | system (apt) | OpenCV's `libGL.so.1` requirement |
| `git` | system (apt) | Required by some pip-installable packages at build time |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| HF Spaces | Runs the Docker image on their infrastructure |
| Local developers | `docker build && docker run` for production-parity testing |

---

## Usage Examples

### Deploy to HF Spaces

```bash
# One-time: create a Space (Docker SDK) at https://huggingface.co/new-space
# Then add the remote:
git remote add space https://huggingface.co/spaces/<your-username>/document-simulator

# Push the current branch as main (HF Spaces deploys from main)
git push space feature/hosting-research:main --force
```

### Test Locally

```bash
# Build (first build: 10–20 min due to torch/paddlepaddle)
docker build -t document-simulator .

# Run — mirrors HF Spaces exactly
docker run --rm -p 7860:7860 document-simulator

# Open
open http://localhost:7860
```

### Rebuild After Code Change (fast — deps layer is cached)

```bash
# Only the app source layer rebuilds (~10 seconds)
docker build -t document-simulator .
docker run --rm -p 7860:7860 document-simulator
```

---

## Future Work

- [ ] CPU-only PyTorch wheel (`torch+cpu` from `download.pytorch.org/whl/cpu`) to cut
  image from ~6 GB to ~4 GB
- [ ] Bake PaddleOCR models into the image to eliminate first-run download after sleep
- [ ] GitHub Actions workflow to auto-push to HF Spaces on merge to `main`
- [ ] HF persistent storage for uploaded files and OCR outputs
- [ ] Multi-architecture build (`linux/amd64,linux/arm64`) for local Apple Silicon testing

---

## References

- [HF Spaces Docker SDK docs](https://huggingface.co/docs/hub/spaces-sdks-docker)
- [Using uv in Docker — Astral docs](https://docs.astral.sh/uv/guides/integration/docker/)
- [docs/hosting-options.md](../hosting-options.md)
