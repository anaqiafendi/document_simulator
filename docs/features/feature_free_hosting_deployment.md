# Feature: Free Hosting Deployment

> **GitHub Issue:** `#24`
> **Status:** `complete`
> **Module:** `deployment` (Dockerfile, GitHub Actions, docs)

---

## Summary

Packages the React SPA + FastAPI backend into a single Docker container and deploys it to Hugging Face Spaces for free public access, with a GitHub Actions workflow for automated CI/CD on every push to `main`.

---

## Motivation

### Problem Statement

The app runs locally only. External users cannot try the synthetic document generator without cloning the repo and running two separate processes. A zero-cost public deployment is needed for demos, testing, and sharing with collaborators.

### Value Delivered

- Anyone can try the app at a public URL with no setup
- Single Docker container — no split frontend/backend hosting complexity
- Free forever on Hugging Face Spaces (Docker SDK, 16GB RAM, no cold-start)
- Automated deployment: push to `main` → live in ~5 minutes

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| Developer | I can share a URL | collaborators can test the app without cloning |
| Reviewer | I can open the hosted app | I can evaluate features without local setup |
| Contributor | I can push to main | the app is automatically deployed |

---

## Acceptance Criteria

- [x] AC-1: `docker build .` completes without errors
- [x] AC-2: `docker run -p 7860:7860 ...` starts the server; `curl localhost:7860/health` returns 200
- [x] AC-3: The React SPA loads at `http://localhost:7860/`
- [x] AC-4: `/api/*` routes are reachable through the container
- [x] AC-5: React Router client-side navigation does not 404 (catch-all serves `index.html`)
- [x] AC-6: `.github/workflows/deploy-hf.yml` exists and pushes to HF Spaces on `main` push
- [x] AC-7: `docs/deployment.md` explains setup end-to-end

---

## Design

### Architecture

```
GitHub (main branch)
    │  git push
    ▼
GitHub Actions (.github/workflows/deploy-hf.yml)
    │  git push --force
    ▼
Hugging Face Spaces (Docker SDK)
    │  docker build
    ▼
┌──────────────────────────────────────────┐
│  python:3.11-slim container (port 7860)  │
│                                          │
│  FastAPI (uvicorn)                       │
│    /api/*    → Python synthesis backend  │
│    /health   → health check              │
│    /assets/* → Static JS/CSS (React)     │
│    /*        → index.html (React Router) │
└──────────────────────────────────────────┘
```

### Docker Multi-Stage Build

```
Stage 1: node:20-slim
  npm ci + npm run build
  Output: webapp/dist/

Stage 2: python:3.11-slim
  uv sync --no-dev (excludes paddleocr, rl)
  COPY webapp/dist/ from stage 1
  CMD: uvicorn on port 7860
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `Dockerfile` | config | Multi-stage build |
| `docker-compose.yml` | config | Local Docker testing |
| `.github/workflows/deploy-hf.yml` | CI/CD | Auto-deploy to HF Spaces |
| `docs/deployment.md` | docs | Human-readable setup guide |
| `app.py` catch-all route | FastAPI | SPA routing support |

### Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `HF_TOKEN` | GitHub Secret | — | HF write token for deploy |
| `HF_USERNAME` | GitHub Secret | — | HF account username |
| `HF_SPACE_NAME` | GitHub Secret | — | Target Space name |
| `DATA_DIR` | env | `./data` | Sample data path in container |

---

## Implementation

### Files

| Path | Role |
|------|------|
| `Dockerfile` | Multi-stage build: Node → Python |
| `docker-compose.yml` | Local Docker testing |
| `.github/workflows/deploy-hf.yml` | CI/CD workflow: push to HF Spaces |
| `docs/deployment.md` | Full deployment guide |
| `src/document_simulator/api/app.py` | Added SPA catch-all route for React Router |

### Key Architectural Decisions

1. **Single container over split hosting** — Serving the React build via FastAPI StaticFiles eliminates the need for a separate CDN or frontend host. One container = one URL, zero CORS issues in production.

2. **Hugging Face Spaces over Render/Railway** — HF Spaces is the only major free platform with no cold-start (unlike Render free tier which spins down after 15 minutes of inactivity), persistent containers, and enough RAM (16GB) for the synthesis + augmentation deps. ML-demo oriented so community discovery is a bonus.

3. **Port 7860** — HF Spaces Docker SDK expects the app on port 7860 by default. Using this port avoids any port-mapping configuration in the Space settings.

4. **Exclude paddleocr/rl from image** — These add ~2GB to the image. The demo use-case is synthetic document generation, which doesn't require OCR or RL. Users who need those features run locally.

5. **Catch-all route for SPA** — `StaticFiles(html=True)` alone doesn't handle deep React Router paths (e.g., `/augmentation`). An explicit `/{full_path:path}` catch-all returning `index.html` solves this cleanly.

### Known Edge Cases & Constraints

- HF Spaces free tier: 2 vCPUs, 16GB RAM, no persistent disk (data written to `/app/data` in container is lost on restart — mount a volume or use HF Datasets for persistence)
- First build on HF Spaces takes 5–10 minutes; subsequent builds use Docker layer cache
- `uv.lock` must be committed for `--frozen` sync to work in Docker

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| Manual: `curl localhost:7860/health` | smoke | 1 | Container starts and responds |
| Manual: browser `localhost:7860/` | smoke | 1 | React SPA loads |

### TDD Cycle Summary

**Red:** No Dockerfile existed; `docker build` would fail.

**Green:** Created multi-stage Dockerfile, verified `app.py` imports cleanly with `uv run python -c "from document_simulator.api.app import app"`.

**Refactor:** Added proper SPA catch-all to `app.py` to replace the previous `StaticFiles(html=True)` mount which broke React Router deep paths.

### How to Run

```bash
# Build
docker build -t document-simulator-demo .

# Smoke test
docker run -p 7860:7860 document-simulator-demo &
sleep 10
curl http://localhost:7860/health
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| Docker | external tool | Container build + run |
| `node:20-slim` | Docker base image | React SPA build stage |
| `python:3.11-slim` | Docker base image | Python runtime stage |
| `uv` | external tool | Fast Python dep install in Docker |
| `ghcr.io/astral-sh/uv:latest` | Docker image | Copies `uv` binary into Python stage |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| HF Spaces | Builds the Dockerfile on every push |
| GitHub Actions | Pushes repo to HF Spaces git remote |

---

## Usage Examples

### Local Docker

```bash
docker build -t document-simulator-demo .
docker run -p 7860:7860 document-simulator-demo
# Open http://localhost:7860
```

### Deploy to Hugging Face Spaces

```bash
# One-time: add HF remote
git remote add hf https://<USER>:<TOKEN>@huggingface.co/spaces/<USER>/<SPACE>
git push hf main --force
# Space URL: https://huggingface.co/spaces/<USER>/<SPACE>
```

---

## Future Work

- [ ] Add HF Datasets volume mount for persistent output storage
- [ ] Add `SPACE_HOST` env var to CORS allowed origins for production
- [ ] Add health check `HEALTHCHECK` instruction to Dockerfile
- [ ] Enable paddleocr in a separate "full" Dockerfile variant
- [ ] Add Render/Fly.io config as alternative deployment targets

---

## References

- [Hugging Face Spaces Docker docs](https://huggingface.co/docs/hub/spaces-sdks-docker)
- [docs/deployment.md](../deployment.md)
- [Feature #20 — React Zone Editor UI](feature_js_zone_editor_ui.md)
