"""Case Knowledge Object contract (Sprint 25.0-A inferred).

This module defines the **canonical frozen shape** of a
``CaseKnowledge`` record. A ``CaseKnowledge`` is the
validated, schema-level intermediate between an
``intake.RawCaseObject`` (pre-knowledge) and a
``corpus.KnowledgeObject`` (final).

Why a separate contract:

    * RawCaseObject carries no ADR-015 fields on purpose
      (it is a "stomach" container, not a Knowledge Object).
    * KnowledgeObject is the final, mutable-under-evolution
      form -- too rigid to act as an ingestion contract.
    * CaseKnowledge fills the gap: the shape every ingestion
      backend MUST emit, regardless of origin.

Fields
------

    case_id            -- unique id assigned at ingestion time
    source             -- free-form origin label (file path,
                           API URL, "manual:abc", ...)
    source_kind        -- one of SOURCE_KIND_* ("intake" /
                           "external" / "operator")
    title              -- short human-readable title
    description        -- longer free-form description
    knowledge_id       -- id of the candidate KO this record
                           is bound to (may equal case_id)
    knowledge_version  -- version of the candidate KO (>=1)
    tags               -- tuple of free-form tags
    linked_assets      -- tuple of asset references
                           (paths, urls, doc ids)
    origin_reference   -- optional bibliographic reference
    created_at         -- ISO timestamp at ingestion time
    created_by         -- free-form operator/system id
    requires_human_review -- V1: always True. Future Sprint
                              may relax.

All collection fields are deep-copied on entry so caller
mutations cannot leak into the frozen record.
"""
from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Tuple


# ---------------------------------------------------------------------------
# Source-kind constants
# ---------------------------------------------------------------------------


SOURCE_KIND_INTAKE: str = "intake"
SOURCE_KIND_EXTERNAL: str = "external"
SOURCE_KIND_OPERATOR: str = "operator"

SOURCE_KIND_ALLOW_LIST: frozenset = frozenset(
    {
        SOURCE_KIND_INTAKE,
        SOURCE_KIND_EXTERNAL,
        SOURCE_KIND_OPERATOR,
    }
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class CaseKnowledgeError(ValueError):
    """Base error for the Case Knowledge ingestion contract."""


# ---------------------------------------------------------------------------
# Default factories
# ---------------------------------------------------------------------------


def _empty_tuple() -> tuple:
    return ()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_case_id() -> str:
    return "CK-" + uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# CaseKnowledge
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CaseKnowledge:
    """The V1 Case Knowledge ingestion contract.

    See module docstring for the field layout. The dataclass
    is frozen; collection fields are deep-copied in
    ``__post_init__`` so the caller cannot mutate the record
    through held references.
    """

    # ---- Identity --------------------------------------------------
    case_id: str = field(default_factory=_new_case_id)

    # ---- Origin ----------------------------------------------------
    source: str = ""
    source_kind: str = SOURCE_KIND_INTAKE

    # ---- Content ---------------------------------------------------
    title: str = ""
    description: str = ""

    # ---- Knowledge binding ----------------------------------------
    knowledge_id: str = ""
    knowledge_version: int = 1

    # ---- Side-band metadata ---------------------------------------
    tags: Tuple[str, ...] = field(default_factory=_empty_tuple)
    linked_assets: Tuple[str, ...] = field(default_factory=_empty_tuple)
    origin_reference: str = ""

    # ---- Operator / runtime ---------------------------------------
    created_at: str = field(default_factory=_now_iso)
    created_by: str = ""
    requires_human_review: bool = True

    # --------------------------------------------------------------
    # Post-init: defensive copies + minimal guards
    # --------------------------------------------------------------

    def __post_init__(self) -> None:
        # Deep-copy collection fields. We treat lists and tuples
        # identically so the caller may pass either.
        for fname in ("tags", "linked_assets"):
            raw = getattr(self, fname)
            if isinstance(raw, list):
                object.__setattr__(self, fname, tuple(copy.deepcopy(raw)))
            elif isinstance(raw, tuple):
                object.__setattr__(self, fname, tuple(copy.deepcopy(raw)))
            elif raw is None:
                object.__setattr__(self, fname, ())

        # String guard.
        if not isinstance(self.case_id, str) or not self.case_id.strip():
            raise CaseKnowledgeError(
                "case_id must be a non-empty string"
            )
        if not isinstance(self.source_kind, str):
            raise CaseKnowledgeError(
                "source_kind must be a string; got "
                + type(self.source_kind).__name__
            )
        if self.source_kind not in SOURCE_KIND_ALLOW_LIST:
            raise CaseKnowledgeError(
                "source_kind must be one of "
                + ", ".join(sorted(SOURCE_KIND_ALLOW_LIST))
                + "; got " + repr(self.source_kind)
            )
        if not isinstance(self.knowledge_version, int) or self.knowledge_version < 1:
            raise CaseKnowledgeError(
                "knowledge_version must be a positive integer (>= 1); got "
                + repr(self.knowledge_version)
            )

    # --------------------------------------------------------------
    # Serialization
    # --------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "source": self.source,
            "source_kind": self.source_kind,
            "title": self.title,
            "description": self.description,
            "knowledge_id": self.knowledge_id,
            "knowledge_version": self.knowledge_version,
            "tags": list(self.tags),
            "linked_assets": list(self.linked_assets),
            "origin_reference": self.origin_reference,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "requires_human_review": self.requires_human_review,
        }

    @staticmethod
    def from_dict(data: dict) -> "CaseKnowledge":
        if not isinstance(data, dict):
            raise CaseKnowledgeError(
                "from_dict expects a dict; got " + type(data).__name__
            )
        kwargs: dict = {}
        for fname in (
            "case_id", "source", "source_kind", "title", "description",
            "knowledge_id", "knowledge_version", "tags", "linked_assets",
            "origin_reference", "created_at", "created_by",
            "requires_human_review",
        ):
            if fname in data:
                kwargs[fname] = data[fname]
        return CaseKnowledge(**kwargs)


# ---------------------------------------------------------------------------
# Convenience builder
# ---------------------------------------------------------------------------


def new_case_knowledge(
    *,
    source: str,
    source_kind: str = SOURCE_KIND_INTAKE,
    title: str = "",
    description: str = "",
    knowledge_id: str = "",
    knowledge_version: int = 1,
    tags=None,
    linked_assets=None,
    origin_reference: str = "",
    created_by: str = "",
    requires_human_review: bool = True,
) -> CaseKnowledge:
    """Construct a ``CaseKnowledge`` with explicit parameters.

    The ``case_id`` is auto-assigned when omitted.
    """
    if source_kind not in SOURCE_KIND_ALLOW_LIST:
        raise CaseKnowledgeError(
            "source_kind must be one of "
            + ", ".join(sorted(SOURCE_KIND_ALLOW_LIST))
            + "; got " + repr(source_kind)
        )
    return CaseKnowledge(
        source=source,
        source_kind=source_kind,
        title=title,
        description=description,
        knowledge_id=knowledge_id,
        knowledge_version=knowledge_version,
        tags=tuple(tags or ()),
        linked_assets=tuple(linked_assets or ()),
        origin_reference=origin_reference,
        created_by=created_by,
        requires_human_review=requires_human_review,
    )
