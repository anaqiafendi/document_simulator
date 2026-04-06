.PHONY: build-frontend dev-api dev-ui

build-frontend:
	cd webapp && npm ci && npm run build

dev-api:
	uv run uvicorn document_simulator.api.app:app --host 0.0.0.0 --port 8000 --reload

dev-ui:
	uv run streamlit run src/document_simulator/ui/app.py
