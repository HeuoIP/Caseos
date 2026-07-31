"""RawCaseObject (Sprint 20.7 spec section 2).

RawCaseObject is NOT a Knowledge Object.

It is the pre-knowledge container that holds unprocessed
incoming information before governance validation and
promotion into the corpus. A RawCaseObject may have empty
or missing fields on purpose: governance is the layer that
decides whether the eventual Knowledge Object is allowed
in, NOT the intake layer.

Required fields:

  id          -- unique identifier assigned by the manager
  source      -- where this information came from
  title       -- short human-readable title
  description -- longer free-form description
  files       -- list of file references (paths, urls, ...)
  notes       -- free-form operator notes
  created_at  -- ISO timestamp at the moment of intake
  status      -- IntakeStatus value

Optional fields:

  candidate_identity_type -- hint, e.g. GoldenCase
  candidate_tags          -- list of free-form tags
  source_reference        -- bibliographic reference

Architecture boundary: a RawCaseObject carries no ADR-015
fields (situation, observation, diagnosis, decision, ...).
Those are produced by the converter, and even then any field
that cannot be filled from the raw case is left as None so
governance can reject the candidate on its own merits."""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from caseos.knowledge.intake.status import IntakeStatus


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class RawCaseObject:
    "A pre-knowledge container for unprocessed information.",

    id: str
    source: str
    title: str
    description: str = ""
    files: list[str] = field(default_factory=list)
    notes: str = ""
    created_at: str = field(default_factory=_now_iso)
    status: IntakeStatus = IntakeStatus.NEW
    # Optional hints and references (not required for intake).
    candidate_identity_type: Optional[str] = None
    candidate_tags: list[str] = field(default_factory=list)
    source_reference: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        "Render the raw case as a plain dict. Status is",
        "serialised as its string value for JSON safety.",
        out = {
            "id": self.id,
            "source": self.source,
            "title": self.title,
            "description": self.description,
            "files": list(self.files),
            "notes": self.notes,
            "created_at": self.created_at,
            "status": self.status.value,
            "candidate_identity_type": self.candidate_identity_type,
            "candidate_tags": list(self.candidate_tags),
            "source_reference": self.source_reference,
        }
        return out

    def copy(self) -> "RawCaseObject":
        "Return a deep copy. The manager never mutates the",
        "stored object; transitions are written as new copies.",
        return copy.deepcopy(self)


def new_raw_case(
    source: str,
    title: str,
    description: str = "",
    files: Optional[list[str]] = None,
    notes: str = "",
    candidate_identity_type: Optional[str] = None,
    candidate_tags: Optional[list[str]] = None,
    source_reference: Optional[str] = None,
    raw_id: Optional[str] = None,
) -> RawCaseObject:
    "Convenience constructor. Assigns a UUID and a NEW status.",
    return RawCaseObject(
        id=raw_id or str(uuid.uuid4()),
        source=source,
        title=title,
        description=description,
        files=list(files or []),
        notes=notes,
        status=IntakeStatus.NEW,
        candidate_identity_type=candidate_identity_type,
        candidate_tags=list(candidate_tags or []),
        source_reference=source_reference,
    )


__all__ = ["RawCaseObject", "new_raw_case"]
