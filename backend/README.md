# CaseOS Backend

Minimal FastAPI skeleton following Clean Architecture layering.

## Layout

```
backend/
??? app/
    ??? api/        # HTTP routers (empty for now)
    ??? core/       # Settings and cross-cutting infrastructure
    ??? models/     # Domain entities (empty for now)
    ??? schemas/    # Pydantic request/response models (empty for now)
    ??? services/   # Use cases / business logic (empty for now)
    ??? utils/      # Generic helpers (empty for now)
    ??? main.py     # FastAPI entry point
```

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Swagger UI: http://localhost:8000/docs
OpenAPI schema: http://localhost:8000/openapi.json
Health probe: http://localhost:8000/health
