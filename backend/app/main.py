"""CaseOS backend entry point. Minimal FastAPI skeleton."""

from fastapi import FastAPI

app = FastAPI(title="CaseOS API", version="0.1.0")


@app.get("/health")
def health() -> dict:
    """Liveness probe used by deploy/monitoring."""
    return {"status": "ok"}
