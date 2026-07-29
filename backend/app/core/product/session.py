"""Session model for the CaseOS Product Layer.

A ``ProductSession`` represents one user's interaction with the product:
their ``ProductRequest``, the in-flight ``ProductResponse``, the
session status, and a per-stage trace. The session survives across
calls so the future Web UI can poll its status.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.core.product.request import ProductRequest
from app.core.product.response import ProductResponse


class SessionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class SessionStage:
    """One stage of a product session's execution."""

    name: str
    status: str = "pending"  # pending | running | ok | error | skipped
    started_at: str = ""
    finished_at: str = ""
    note: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProductSession:
    """One user's product interaction."""

    request: ProductRequest
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: SessionStatus = SessionStatus.PENDING
    response: ProductResponse | None = None
    stages: list[SessionStage] = field(default_factory=list)
    error: str | None = None
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    # ---- helpers ----

    def start_stage(self, name: str, note: str = "") -> SessionStage:
        s = SessionStage(
            name=name,
            status="running",
            started_at=_now_iso(),
            finished_at="",
            note=note,
        )
        self.stages.append(s)
        self.updated_at = _now_iso()
        return s

    def finish_stage(self, stage: SessionStage, status: str = "ok", note: str = "") -> None:
        stage.status = status
        stage.finished_at = _now_iso()
        if note:
            stage.note = note
        self.updated_at = _now_iso()

    def to_summary(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "status": self.status.value,
            "error": self.error,
            "stages": [
                {
                    "name": s.name,
                    "status": s.status,
                    "duration": _duration(s.started_at, s.finished_at),
                }
                for s in self.stages
            ],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def _duration(started: str, finished: str) -> str:
    if not started or not finished:
        return ""
    try:
        t0 = datetime.fromisoformat(started.replace("Z", "+00:00"))
        t1 = datetime.fromisoformat(finished.replace("Z", "+00:00"))
        return f"{(t1 - t0).total_seconds():.3f}s"
    except Exception:
        return ""


__all__ = ["ProductSession", "SessionStage", "SessionStatus"]