# CaseOS Tech Stack

> Last reviewed 2026-07-30 (Sprint 12 Pivot Cleanup).
> Reflects the current implementation, not future wishlist.

## Frontend (future)

- React
- Next.js
- TailwindCSS

## Backend

- Python 3.12 (declared in Sprint 1)
- FastAPI (declared; surface lands in Sprint 13)
- Pydantic
- python-dotenv

## Database (declared, not yet built)

- PostgreSQL
- pgvector (for future vector retrieval; V1 uses local retriever)
- SQLAlchemy (declared in requirements.txt; not yet wired)

## Storage

- Alibaba OSS (declared for image storage; V1 keeps images in
  "data/images/cases/" locally, Git LFS intended).

## Vision

- Qwen3.7-Plus via DashScope OpenAI-compatible API
  (wired in "backend/app/services/vision/providers/qwen.py").
- Vision Prompt: "backend/prompts/vision_prompt_v2.md" (V3 output
  shape, per ADR-008).

## LLM (declared, V1 uses template renderers)

- The text-rendering side of Strategy Agent and Explain Agent is
  currently a deterministic template (see Sprint 9). The LLM
  swap-in is Sprint 15. The intended provider for V1 is the same
  Qwen3.7-Plus endpoint used for vision; the product Blueprint V1
  does NOT name a specific LLM.
- "MiniMax M3" was a V1 placeholder. It is removed.

## Image (declared, V1 has no image generation)

- The Blueprint V1 V1 has no image generation step. Krea and
  ComfyUI are deferred.

## Deploy (declared, no Dockerfile yet)

- Docker is declared in the Blueprint; the Dockerfile lands in
  Sprint 13.

## GPU (declared, not used in V1)

- DuanNaoYun is a future-self-host option for when CaseOS runs
  its own embeddings. V1 uses the cloud Vision API.
