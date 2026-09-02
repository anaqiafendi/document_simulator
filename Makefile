.PHONY: build-frontend dev-api dev-ui test test-receipts prior logos

build-frontend:
	cd webapp && npm ci && npm run build

dev-api:
	uv run uvicorn document_simulator.api.app:app --host 0.0.0.0 --port 8000 --reload

dev-ui:
	uv run streamlit run src/document_simulator/ui/app.py

# WeasyPrint's native deps are not on the macOS loader path by default; without
# this every receipt-synthesis import fails at collection time.
DYLD_FIX := DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib

# --active makes uv honour an already-activated venv. Without it, uv prefers a
# per-worktree .venv, which in a fresh git worktree is empty -- so every import
# fails even though the primary checkout is fully installed.
UV := $(DYLD_FIX) uv run --active

test:
	$(UV) pytest -m "not slow" -q

test-receipts:
	$(UV) pytest tests/synthesis/receipts/ -q --no-cov

# Rebuild the layout prior from the scraped ReceiptFaker corpus.
prior:
	$(UV) python -m document_simulator.data.receiptfaker.export_prior

# Populate the shared logo cache (~750 images, ~30s). Stored outside the repo so
# it survives worktrees; safe to re-run, existing files are skipped.
logos:
	$(UV) python -m document_simulator.data.receiptfaker.logos
