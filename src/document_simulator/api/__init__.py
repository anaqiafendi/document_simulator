import uvicorn


def run() -> None:
    """Entry point for the document-simulator-api script."""
    uvicorn.run(
        "document_simulator.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
