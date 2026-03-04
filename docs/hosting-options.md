# Hosting Options for Document Simulator

Streamlit Community Cloud is free but slow and resource-constrained. This document
covers the best alternatives for hosting the Document Simulator Streamlit app.

## App Profile

| Property | Value |
|---|---|
| Runtime | Python 3.11, uv-managed |
| Key dependencies | augraphy, opencv-python, torch (CPU), paddleocr, stable-baselines3, pymupdf |
| Total packages | ~270 (647 KB uv.lock) |
| Minimum RAM | ~2–3 GB at import; 4 GB comfortable |
| Docker image size | ~4–6 GB (torch + paddlepaddle dominate) |
| GPU required | No (CPU-only for basic use) |

---

## Recommended: Hugging Face Spaces (free tier)

**Best for:** prototyping, demos, internal tools — zero cost.

HF Spaces Docker SDK gives **2 vCPU / 16 GB RAM / 50 GB disk for free** — the only
platform where the full stack runs without paying anything.

### Deployment steps

1. Create a Space at [huggingface.co/new-space](https://huggingface.co/new-space),
   choose **Docker** SDK.

2. Add a `Dockerfile` at the repo root:

```dockerfile
FROM python:3.11-slim

# Install system dependency for OpenCV
RUN apt-get update && apt-get install -y libgl1 && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never

# Install deps first (layer-cached)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy app source
COPY src/ ./src/
COPY data/ ./data/
COPY .streamlit/ ./.streamlit/

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 7860
CMD ["streamlit", "run", "src/document_simulator/ui/app.py", \
     "--server.port=7860", "--server.address=0.0.0.0"]
```

3. Add `.streamlit/config.toml`:

```toml
[server]
enableCORS = false
enableXsrfProtection = false
```

4. Push to the Space's git remote (HF provides a `git remote add` command).

### Caveats

- **Port must be 7860** (not 8501 — HF Spaces requirement).
- **Sleeps after ~30 min idle** on the free tier; wake time 30–120 s.
- **Ephemeral disk** — PaddleOCR model files re-download on every wake unless baked
  into the Docker image or you pay for persistent storage ($5–$100/month).
- Streamlit SDK is deprecated on HF Spaces — always use the Docker SDK.

---

## Best for Low-Cost Always-On: Fly.io (~$10–15/month)

**Best for:** always-on production with no sleep, minimal ops overhead.

### Deployment steps

1. Install flyctl: `brew install flyctl` (macOS) or see [fly.io/docs](https://fly.io/docs/hands-on/install-flyctl/).

2. `fly auth login && fly launch` (pick `No` when asked to deploy immediately).

3. Edit the generated `fly.toml`:

```toml
app = "document-simulator"
primary_region = "lhr"  # or nearest region

[build]
  dockerfile = "Dockerfile"

[http_service]
  internal_port = 8501
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 1   # keeps one instance warm — no cold starts

[[vm]]
  memory = "4gb"
  cpu_kind = "shared"
  cpus = 2
```

4. `fly deploy`

### Cost

`shared-cpu-2x` + 4 GB RAM running 24/7 ≈ **$10–15/month**. Add $5 for a volume if
you need persistent file storage.

### Dockerfile (shared with HF Spaces, just change the port)

Use the same Dockerfile as above but change `EXPOSE 7860` → `EXPOSE 8501` and update
the `CMD` to use `--server.port=8501`.

---

## Best DX for Paid Production: Railway.app (~$35/month)

**Best for:** teams who want GitHub push-to-deploy with zero ops knowledge.

Railway natively supports uv (`pyproject.toml` detected automatically), connects to
GitHub for auto-deploy on push, and never sleeps.

### Deployment steps

1. Create a new project at [railway.app](https://railway.app), connect your GitHub repo.
2. Railway auto-detects the `Dockerfile` — no config needed.
3. Set the environment variable `PORT=8501` and add a custom start command if needed:
   `streamlit run src/document_simulator/ui/app.py --server.port=$PORT --server.address=0.0.0.0`
4. Add a domain under **Settings → Networking**.

### Cost

Hobby plan ($5/month) + resource usage ($10.01/GB-RAM/month):
- 3 GB RAM ≈ $30 in resource charges
- **Total ≈ $35/month**

---

## Platform Summary

| Platform | Min Viable Cost | RAM | Free Tier | Cold Starts | Difficulty |
|---|---|---|---|---|---|
| **Hugging Face Spaces** | **$0** | **16 GB free** | Yes (sleeps after idle) | Yes (~30–120 s) | Easy-Medium |
| **Fly.io** | ~$10–15/month | 4 GB | 256 MB (too small) | Mitigated with `min=1` | Medium |
| **Railway** | ~$35/month | Up to 8 GB | $5 trial credit | None | **Easy** |
| **Render** | $25–$85/month | 2–4 GB | OOMs (512 MB) | None on paid | Easy-Medium |
| **DigitalOcean** | $50/month | 4 GB | None | None | Easy-Medium |
| **Cloud Run** | ~$25–35/month | Up to 32 GB | Tiny | Bad without min=1 | Medium-Hard |
| **App Runner** | ~$56/month | Up to 12 GB | None | None | Hard (WebSocket issues) |
| **Azure CA** | ~$20–30/month | Up to 8 GB | Tiny | Bad without min=1 | Hard |

### Avoid

- **AWS App Runner** — documented WebSocket incompatibility with Streamlit.
- **Render free tier** — 512 MB RAM, will OOM on import.
- **Streamlit Community Cloud** — cold starts, 1 GB RAM limit, very slow for heavy deps.

---

## Docker Image Size Optimisation

Regardless of platform, trim the image to reduce build times and cold starts:

```dockerfile
# Use CPU-only torch to save ~1.5 GB vs the default GPU wheel
# Add to your pip install / uv sync step:
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

Or pin `torch` to a CPU-only wheel in `pyproject.toml`:
```toml
[tool.uv.sources]
torch = { index = "pytorch-cpu" }
torchvision = { index = "pytorch-cpu" }

[[tool.uv.index]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"
explicit = true
```

This alone cuts the Docker image from ~5–6 GB to ~3.5–4 GB.
