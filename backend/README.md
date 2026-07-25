# CaseOS Backend

Minimal FastAPI skeleton following Clean Architecture layering.

## Requirements

- Python 3.12

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

## Run manually

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Swagger UI: http://localhost:8000/docs
OpenAPI schema: http://localhost:8000/openapi.json
Health probe: http://localhost:8000/health

## Convenience scripts

| Script | Purpose |
| --- | --- |
| `backend/scripts/run_dev.ps1` | Foreground development runner. |
| `backend/scripts/run_dev_hidden.vbs` | Hidden launcher used by the scheduled task. |
| `backend/scripts/register_startup.ps1` | Registers `CaseOS-Backend-Dev` to launch at logon (hidden, restart on failure). |
| `backend/scripts/unregister_startup.ps1` | Removes the scheduled task and stops any running uvicorn. |

### Auto-start at logon (hidden window)

```powershell
powershell -ExecutionPolicy Bypass -File backend\scripts\register_startup.ps1
```

To disable later:

```powershell
powershell -ExecutionPolicy Bypass -File backend\scripts\unregister_startup.ps1
```

After registration, the FastAPI skeleton boots silently in the background and
serves Swagger at `http://localhost:8000/docs` whenever you sign in.
