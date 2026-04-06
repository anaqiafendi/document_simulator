# Deployment Guide — Document Simulator

This guide covers deploying the Document Simulator (React SPA + FastAPI backend) to Hugging Face Spaces for free public access.

---

## Architecture

The app ships as a **single Docker container**:

```
┌─────────────────────────────────────┐
│  Docker Container (python:3.11-slim) │
│                                      │
│  FastAPI (uvicorn, port 7860)        │
│    ├── /api/*       → Python backend │
│    ├── /health      → health check   │
│    └── /*           → React SPA      │
│         (served from webapp/dist/)   │
└─────────────────────────────────────┘
```

A **multi-stage Dockerfile** builds the React SPA in a Node.js stage, then copies the compiled assets into the Python runtime stage. No separate frontend server is needed in production.

---

## Hosting: Hugging Face Spaces (Free)

**Why Hugging Face Spaces?**
- Free Docker Spaces with 16GB RAM, 2 vCPUs
- No cold-start issues (persistent containers)
- ML-friendly — designed for demo apps
- Git-based deployment (just `git push`)
- Persistent storage available

### One-time Setup

1. **Create a Hugging Face account** at https://huggingface.co

2. **Create a new Space:**
   - Go to https://huggingface.co/new-space
   - SDK: **Docker**
   - Visibility: Public
   - Name: e.g., `document-simulator`

3. **Add a `README.md` for the Space** (HF Spaces requires it):
   ```markdown
   ---
   title: Document Simulator
   emoji: 📄
   colorFrom: blue
   colorTo: purple
   sdk: docker
   pinned: false
   ---
   ```
   Place this at the repo root (this repo's README.md already works).

4. **Add GitHub Secrets** (repo Settings → Secrets → Actions):
   | Secret | Value |
   |--------|-------|
   | `HF_TOKEN` | Your HF write token (https://huggingface.co/settings/tokens) |
   | `HF_USERNAME` | Your HF username |
   | `HF_SPACE_NAME` | The Space name (e.g., `document-simulator`) |

5. **Push to main** — the GitHub Actions workflow (`.github/workflows/deploy-hf.yml`) automatically pushes to the Space and triggers a Docker build.

### Manual Deploy (without CI/CD)

```bash
# Add HF remote
git remote add hf https://<YOUR_HF_USERNAME>:<YOUR_HF_TOKEN>@huggingface.co/spaces/<YOUR_HF_USERNAME>/<YOUR_SPACE_NAME>

# Push
git push hf main --force
```

The Space will appear at: `https://huggingface.co/spaces/<username>/<space-name>`

---

## Local Docker Testing

### Prerequisites
- Docker Desktop installed and running

### Build and run

```bash
# Build the image (takes ~5 minutes on first run)
docker build -t document-simulator-demo .

# Run
docker run -p 7860:7860 -v $(pwd)/data:/app/data document-simulator-demo

# Open in browser
open http://localhost:7860
```

### With docker-compose

```bash
docker-compose up --build
# Open http://localhost:7860
```

### Health check

```bash
curl http://localhost:7860/health
# {"status": "ok", "version": "0.1.0"}
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_DIR` | `./data` | Path to sample PDFs and data |
| `OUTPUT_DIR` | `./output` | Path for generated output |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

Set these in HF Space Settings → Variables and secrets (for sensitive values use secrets).

---

## Excluded Dependencies (Slim Build)

The Docker image **excludes** these optional extras to keep the image under 1GB:
- `paddleocr` / `paddlepaddle` — OCR engine (heavy, ~500MB)
- `stable-baselines3` / `gymnasium` — RL training

The **synthesis module, augmentation, and document preview** are fully included.

To include all features, change the `uv sync` line in the Dockerfile:
```dockerfile
# Full build (warning: ~3GB image):
RUN uv sync --no-dev --frozen --extra ui
```

---

## Updating the Deployment

Push to `main` — the GitHub Action handles the rest:

```bash
git push origin main
```

HF Spaces rebuilds the Docker image automatically (~3-5 minutes).
