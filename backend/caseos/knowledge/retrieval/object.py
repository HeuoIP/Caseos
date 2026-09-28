"""Knowledge Retrieval Contract Objects V1 (Sprint 24.0-A).

This module declares the **public I/O contracts** for the
CaseOS Retrieval layer:

    * ``RetrievalQuery``  -- what the caller asks for
    * ``RetrievalHit``    -- one matched Knowledge Object
                             + score + matched fields
    * ``RetrievalResult`` -- the output envelope of a
                             single retrieval call

All three are ``@dataclass(frozen=True)`` so they can be
freely shared across threads, hash-compared in tests, and
serialized without mutation hazards. Collection-typed
fields are **deep-copied in ``__post_init__``** so caller
mutations cannot leak into the record.

This module is the **contract layer**; the keyword engine
that consumes ``RetrievalQuery`` and produces
``RetrievalResult`` lives in
``caseos.knowledge.retrieval.engine``.

Architecture boundary (Sprint 24.0-A spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This module MAY import from:
        * caseos.knowledge.object  (KO schema)
        * stdlib
"""
from __future__ import annotations

import copy
import dataclasses
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Default factories
# ---------------------------------------------------------------------------


def _empty_list() -> list:
    return []


def _empty_dict() -> dict:
    return {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_query_id() -> str:
    return "QRY-" + uuid.uuid4().hex[:12]


def _new_hit_id() -> str:
    return "HIT-" + uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class RetrievalContractError(ValueError):
    """Base error for the retrieval contract layer."""


# ---------------------------------------------------------------------------
# RetrievalQuery
# ---------------------------------------------------------------------------


# Default constants -- see schema.py for the allow-lists.
DEFAULT_MATCH_MODE = "any"
DEFAULT_SORT_BY = "score"
DEFAULT_SORT_ORDER = "desc"
DEFAULT_LIMIT = 20


@dataclass(frozen=True)
class RetrievalQuery:
    """The input contract for a retrieval call.

    Field groups:

        Identity
            query_id, version

        Input
            query_text         -- free-form text; optional
            query_fields       -- which KO fields to scan
                                  (defaults to textual fields)
            filters            -- exact-match dict over KO fields
            match_mode         -- "any" / "all" / "exact"
            limit              -- 1..1000

        Result shaping
            sort_by            -- "score" | "knowledge_id"
                                  | "version" | "created_at"
            sort_order         -- "asc" | "desc"
            required_attributes -- KO must have non-empty value
                                   for each named attribute slot
            bound_domain_ids   -- KO's binding to one of these
                                   domains is required

        Metadata
            created_at, created_by
    """

    # ---- Identity --------------------------------------------------
    query_id: str = field(default_factory=_new_query_id)
    version: int = 1

    # ---- Input -----------------------------------------------------
    query_text: str = ""
    query_fields: List[str] = field(default_factory=_empty_list)
    filters: Dict[str, Any] = field(default_factory=_empty_dict)
    match_mode: str = DEFAULT_MATCH_MODE
    limit: int = DEFAULT_LIMIT

    # ---- Result shaping -------------------------------------------
    sort_by: str = DEFAULT_SORT_BY
    sort_order: str = DEFAULT_SORT_ORDER
    required_attributes: List[str] = field(default_factory=_empty_list)
    bound_domain_ids: List[str] = field(default_factory=_empty_list)

    # ---- Metadata --------------------------------------------------
    created_at: str = field(default_factory=_now_iso)
    created_by: str = ""

    # --------------------------------------------------------------
    # Post-init: defensive copy + minimal guards
    # --------------------------------------------------------------

    def __post_init__(self) -> None:
        # Deep-copy every collection-typed field so caller
        # mutations cannot leak into the frozen record.
        for fname in (
            "query_fields",
            "required_attributes",
            "bound_domain_ids",
        ):
            raw = getattr(self, fname)
            if isinstance(raw, list):
                object.__setattr__(self, fname, copy.deepcopy(raw))
            elif isinstance(raw, tuple):
                object.__setattr__(self, fname, copy.deepcopy(list(raw)))

        raw_filters = self.filters
        if isinstance(raw_filters, dict):
            object.__setattr__(self, "filters", copy.deepcopy(raw_filters))
        elif raw_filters is None:
            object.__setattr__(self, "filters", {})

        # Minimal identity guard; full validation lives in
        # ``RetrievalValidator`` (Q1..Q8).
        if not isinstance(self.query_id, str) or not self.query_id.strip():
            raise RetrievalContractError(
                "query_id must be a non-empty string"
            )
        if not isinstance(self.version, int) or self.version < 1:
            raise RetrievalContractError(
                "version must be a positive integer (>= 1); got "
                + repr(self.version)
            )

    # --------------------------------------------------------------
    # Serialization
    # --------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "version": self.version,
            "query_text": self.query_text,
            "query_fields": list(self.query_fields),
            "filters": dict(self.filters),
            "match_mode": self.match_mode,
            "limit": self.limit,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
            "required_attributes": list(self.required_attributes),
            "bound_domain_ids": list(self.bound_domain_ids),
            "created_at": self.created_at,
            "created_by": self.created_by,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "RetrievalQuery":
        if not isinstance(data, dict):
            raise RetrievalContractError(
                "from_dict expects a dict; got " + type(data).__name__
            )
        kwargs: dict[str, Any] = {}
        for fname in (
            "query_id",
            "version",
            "query_text",
            "query_fields",
            "filters",
            "match_mode",
            "limit",
            "sort_by",
            "sort_order",
            "required_attributes",
            "bound_domain_ids",
            "created_at",
            "created_by",
        ):
            if fname in data:
                kwargs[fname] = data[fname]
        # Apply defaults if neither caller nor defaults provided.
        if "match_mode" not in kwargs:
            kwargs["match_mode"] = DEFAULT_MATCH_MODE
        if "limit" not in kwargs:
            kwargs["limit"] = DEFAULT_LIMIT
        if "sort_by" not in kwargs:
            kwargs["sort_by"] = DEFAULT_SORT_BY
        if "sort_order" not in kwargs:
            kwargs["sort_order"] = DEFAULT_SORT_ORDER
        return RetrievalQuery(**kwargs)


# ---------------------------------------------------------------------------
# RetrievalHit
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RetrievalHit:
    """One matched Knowledge Object in a ``RetrievalResult``.

    Fields:

        hit_id                     -- unique id (HIT-...)
        knowledge_id               -- matched KO identity
        knowledge_version          -- matched KO version
        match_score                -- 0.0..1.0, higher is better
        matched_fields             -- the KO fields that matched
                                       the query
        matched_snippets           -- per-field short excerpt
                                       of the matched value
        knowledge_object_snapshot  -- a shallow dict view of the
                                       KO at retrieval time. It is
                                       deep-copied on entry.
    """

    hit_id: str = field(default_factory=_new_hit_id)
    knowledge_id: str = ""
    knowledge_version: int = 1
    match_score: float = 0.0
    matched_fields: List[str] = field(default_factory=_empty_list)
    matched_snippets: Dict[str, str] = field(default_factory=_empty_dict)
    knowledge_object_snapshot: Dict[str, Any] = field(
        default_factory=_empty_dict
    )

    def __post_init__(self) -> None:
        # Defensive deep-copy on collection fields.
        mf = self.matched_fields
        if isinstance(mf, list):
            object.__setattr__(self, "matched_fields", copy.deepcopy(mf))
        elif isinstance(mf, tuple):
            object.__setattr__(
                self, "matched_fields", copy.deepcopy(list(mf))
            )

        ms = self.matched_snippets
        if isinstance(ms, dict):
            object.__setattr__(
                self, "matched_snippets", copy.deepcopy(ms)
            )

        snap = self.knowledge_object_snapshot
        if isinstance(snap, dict):
            object.__setattr__(
                self, "knowledge_object_snapshot", copy.deepcopy(snap)
            )
        elif snap is None:
            object.__setattr__(
                self, "knowledge_object_snapshot", {}
            )

        # Score guard.
        if not isinstance(self.match_score, (int, float)):
            raise RetrievalContractError(
                "match_score must be a number; got "
                + type(self.match_score).__name__
            )
        if self.match_score < 0.0 or self.match_score > 1.0:
            raise RetrievalContractError(
                "match_score must be between 0.0 and 1.0; got "
                + repr(self.match_score)
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "hit_id": self.hit_id,
            "knowledge_id": self.knowledge_id,
            "knowledge_version": self.knowledge_version,
            "match_score": self.match_score,
            "matched_fields": list(self.matched_fields),
            "matched_snippets": dict(self.matched_snippets),
            "knowledge_object_snapshot": dict(
                self.knowledge_object_snapshot
            ),
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "RetrievalHit":
        if not isinstance(data, dict):
            raise RetrievalContractError(
                "from_dict expects a dict; got " + type(data).__name__
            )
        kwargs: dict[str, Any] = {}
        for fname in (
            "hit_id",
            "knowledge_id",
            "knowledge_version",
            "match_score",
            "matched_fields",
            "matched_snippets",
            "knowledge_object_snapshot",
        ):
            if fname in data:
                kwargs[fname] = data[fname]
        return RetrievalHit(**kwargs)


# ---------------------------------------------------------------------------
# RetrievalResult
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RetrievalResult:
    """The output envelope of a retrieval call.

    Fields:

        query_id           -- id of the originating query
        success            -- True iff the engine ran cleanly
        total_hits         -- number of hits in ``hits``
        hits               -- tuple of ``RetrievalHit``
        execution_time_ms  -- how long the engine took
        created_at         -- ISO timestamp
    """

    query_id: str = ""
    success: bool = False
    total_hits: int = 0
    hits: Tuple[RetrievalHit, ...] = ()
    execution_time_ms: float = 0.0
    created_at: str = field(default_factory=_now_iso)

    def __post_init__(self) -> None:
        # Defensive deep-copy / freeze on collection fields.
        hits_raw = self.hits
        if isinstance(hits_raw, list):
            frozen = tuple(hits_raw)
            object.__setattr__(self, "hits", frozen)
        elif isinstance(hits_raw, tuple):
            object.__setattr__(self, "hits", tuple(hits_raw))

        # Cross-field consistency.
        if self.total_hits != len(self.hits):
            raise RetrievalContractError(
                "total_hits="
                + str(self.total_hits)
                + " does not match len(hits)="
                + str(len(self.hits))
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "success": self.success,
            "total_hits": self.total_hits,
            "hits": tuple(h.to_dict() for h in self.hits),
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "RetrievalResult":
        if not isinstance(data, dict):
            raise RetrievalContractError(
                "from_dict expects a dict; got " + type(data).__name__
            )
        kwargs: dict[str, Any] = {}
        for fname in (
            "query_id",
            "success",
            "total_hits",
            "execution_time_ms",
            "created_at",
        ):
            if fname in data:
                kwargs[fname] = data[fname]
        raw_hits = data.get("hits", ())
        hits: list[RetrievalHit] = []
        if isinstance(raw_hits, (list, tuple)):
            for h in raw_hits:
                if isinstance(h, RetrievalHit):
                    hits.append(h)
                elif isinstance(h, dict):
                    hits.append(RetrievalHit.from_dict(h))
        kwargs["hits"] = hits
        return RetrievalResult(**kwargs)


__all__ = [
    "RetrievalQuery",
    "RetrievalHit",
    "RetrievalResult",
    "RetrievalContractError",
    "DEFAULT_MATCH_MODE",
    "DEFAULT_SORT_BY",
    "DEFAULT_SORT_ORDER",
    "DEFAULT_LIMIT",
]
