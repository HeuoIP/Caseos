"""CaseOS backend entry point.

Minimal FastAPI application that exposes the Swagger UI at /docs.
"""

from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.get("/health", tags=["system"])
def health() -> dict:
    """Liveness probe used by deploy and monitoring."""
    return {"status": "ok"}
