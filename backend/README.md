# CaseOS Backend

Minimal FastAPI skeleton.

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Health check

```
GET /health -> {"status": "ok"}
```
