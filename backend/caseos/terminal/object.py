"""Terminal data carriers (Sprint 26.0-A, Terminal MVP V1).

This module declares the V1 product-facing data contracts for
the Terminal entry point. A Terminal MVP V1:

    * receives a ``TerminalRequest`` from the user,
    * validates it (T1..T8 in ``validator.py``),
    * turns it into a ``TerminalQuery`` (in ``query_builder.py``),
    * runs the existing ``RetrievalPipeline``,
    * returns a ``TerminalResult`` carrying the cases.

The contracts are intentionally narrow. They do NOT contain any
business logic; they are immutable envelopes. V1 supports a
partial-information flow -- the only required fields are
``request_id``, ``site_type``, and (site_description OR
uploaded_asset_ids); everything else is optional.

Architecture boundary (Sprint 26.0-A spec section 7):

    This module imports from stdlib only.
    It does NOT import from caseos.intelligence.*, caseos.brain.*,
    caseos.knowledge.evolution, caseos.knowledge.governance,
    caseos.knowledge.feedback, caseos.knowledge.intake,
    caseos.knowledge.corpus, or any LLM / VLM / embedding SDK.
"""
from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional, Tuple


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_request_id() -> str:
    return "TR-" + uuid.uuid4().hex[:12]


def _new_query_id() -> str:
    return "TQ-" + uuid.uuid4().hex[:12]


def _empty_tuple() -> Tuple[Any, ...]:
    return ()


@dataclass(frozen=True)
class TerminalRequest:
    """The user-facing intake record for Terminal V1.

    Required (validator T1..T4):
            request_id            unique id (auto-assigned if empty)
            site_type             non-empty string
            site_description      text OR uploaded_asset_ids non-empty

    Optional:
            site_area             numeric; must be > 0 when set
            user_requirements     free-form text
            age_range             free-form age label
            preferred_functions   tuple of function names; no empties
            preferred_style       single style name
            preferred_theme       single theme name
            uploaded_asset_ids    tuple of asset ids; no empties
            locale                locale tag
            created_at            ISO timestamp; auto-filled if empty
    """

    # ---- Identity ---------------------------------------------------
    request_id: str = field(default_factory=_new_request_id)

    # ---- Site basics -----------------------------------------------
    site_type: str = ""
    site_description: str = ""
    site_area: Optional[float] = None
    user_requirements: str = ""

    # ---- User / audience -------------------------------------------
    age_range: str = ""

    # ---- Preferences ------------------------------------------------
    preferred_functions: Tuple[str, ...] = field(default_factory=_empty_tuple)
    preferred_style: str = ""
    preferred_theme: str = ""

    # ---- Assets ----------------------------------------------------
    uploaded_asset_ids: Tuple[str, ...] = field(default_factory=_empty_tuple)

    # ---- Metadata --------------------------------------------------
    locale: str = ""
    created_at: str = field(default_factory=_now_iso)

    def __post_init__(self) -> None:
        for fname in ("preferred_functions", "uploaded_asset_ids"):
            raw = getattr(self, fname)
            if isinstance(raw, list):
                object.__setattr__(self, fname, tuple(copy.deepcopy(raw)))
            elif isinstance(raw, tuple):
                object.__setattr__(self, fname, tuple(copy.deepcopy(raw)))
            elif raw is None:
                object.__setattr__(self, fname, ())

        if not isinstance(self.request_id, str) or not self.request_id:
            object.__setattr__(self, "request_id", _new_request_id())

        if not isinstance(self.created_at, str) or not self.created_at:
            object.__setattr__(self, "created_at", _now_iso())

        if self.site_area is not None and not isinstance(self.site_area, (int, float)):
            try:
                coerced = float(self.site_area)
                object.__setattr__(self, "site_area", coerced)
            except (TypeError, ValueError):
                pass

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "site_type": self.site_type,
            "site_description": self.site_description,
            "site_area": self.site_area,
            "user_requirements": self.user_requirements,
            "age_range": self.age_range,
            "preferred_functions": list(self.preferred_functions),
            "preferred_style": self.preferred_style,
            "preferred_theme": self.preferred_theme,
            "uploaded_asset_ids": list(self.uploaded_asset_ids),
            "locale": self.locale,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: dict) -> "TerminalRequest":
        if not isinstance(data, dict):
            raise TypeError(
                "from_dict expects a dict; got " + type(data).__name__
            )
        kwargs: dict = {}
        for fname in (
            "request_id", "site_type", "site_description", "site_area",
            "user_requirements", "age_range", "preferred_functions",
            "preferred_style", "preferred_theme", "uploaded_asset_ids",
            "locale", "created_at",
        ):
            if fname in data:
                kwargs[fname] = data[fname]
        return TerminalRequest(**kwargs)


@dataclass(frozen=True)
class TerminalQuery:
    """The Terminal-side query contract.

    A ``TerminalQuery`` is the deterministic, query-builder-only
    artefact derived from a validated ``TerminalRequest``. It is
    the only thing the ``TerminalService`` consumes; the request
    is no longer referenced downstream.

    Fields:
            query_id                unique id (auto-assigned)
            query_text              deterministic concat of site fields
            structured_constraints  tuple of (key, value) pairs; the
                                    keys map to KnowledgeObject fields
                                    (e.g. ``site_type``, ``theme``,
                                    ``style``). Consumed by
                                    ``RetrievalQuery.filters``.
            semantic_concepts       tuple of free-form concept strings
                                    (theme / style / function tags)
                                    the caller asked for. NOT consumed
                                    by V1 (no semantic engine wired in);
                                    kept so the contract is forward-ready.
            limit                   Top-K cap passed to RetrievalQuery.
    """

    query_id: str = field(default_factory=_new_query_id)
    query_text: str = ""
    structured_constraints: Tuple[Tuple[str, Any], ...] = field(
        default_factory=_empty_tuple,
    )
    semantic_concepts: Tuple[str, ...] = field(default_factory=_empty_tuple)
    limit: int = 1

    def __post_init__(self) -> None:
        sc = self.structured_constraints
        if isinstance(sc, dict):
            object.__setattr__(
                self,
                "structured_constraints",
                tuple((k, copy.deepcopy(v)) for k, v in sc.items()),
            )
        elif isinstance(sc, list):
            object.__setattr__(
                self,
                "structured_constraints",
                tuple((k, copy.deepcopy(v)) for k, v in sc),
            )
        elif sc is None:
            object.__setattr__(self, "structured_constraints", ())

        conc = self.semantic_concepts
        if isinstance(conc, list):
            object.__setattr__(
                self, "semantic_concepts", tuple(copy.deepcopy(conc)),
            )
        elif conc is None:
            object.__setattr__(self, "semantic_concepts", ())

        if not isinstance(self.query_id, str) or not self.query_id:
            object.__setattr__(self, "query_id", _new_query_id())

    def filters_dict(self) -> dict:
        return dict(self.structured_constraints)

    def to_dict(self) -> dict:
        return {
            "query_id": self.query_id,
            "query_text": self.query_text,
            "structured_constraints": [
                [k, v] for k, v in self.structured_constraints
            ],
            "semantic_concepts": list(self.semantic_concepts),
            "limit": self.limit,
        }


@dataclass(frozen=True)
class TerminalResult:
    """The Terminal output contract.

    ``cases`` is a fresh view over ``retrieval_result.hits``.
    ``total_hits`` mirrors ``retrieval_result.total_hits`` so the
    caller does not have to reach through ``retrieval_result``.

    All fields are immutable. The TerminalService NEVER mutates
    the input knowledge_objects or the upstream RetrievalResult;
    the result is a pure projection.
    """

    request_id: str = ""
    query: Optional[TerminalQuery] = None
    retrieval_result: Any = None
    total_hits: int = 0
    cases: Tuple[Any, ...] = field(default_factory=_empty_tuple)
    success: bool = False
    failure_reason: str = ""
    created_at: str = field(default_factory=_now_iso)

    def __post_init__(self) -> None:
        raw_cases = self.cases
        if isinstance(raw_cases, list):
            object.__setattr__(self, "cases", tuple(raw_cases))
        elif raw_cases is None:
            object.__setattr__(self, "cases", ())

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "query": self.query.to_dict() if self.query is not None else None,
            "retrieval_result": (
                self.retrieval_result.to_dict()
                if self.retrieval_result is not None else None
            ),
            "total_hits": self.total_hits,
            "cases": [c.to_dict() for c in self.cases],
            "success": self.success,
            "failure_reason": self.failure_reason,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class TerminalValidationResult:
    """Outcome of validating a TerminalRequest.

    Mirrors the style used elsewhere in CaseOS (e.g.
    ``IngestionValidationResult``). The validator stamps one of
    the rule ids T1..T8 on rejection (see ``contract.py``).
    """

    valid: bool = False
    rule_id: str = ""
    reason: str = ""
    checked_at: str = field(default_factory=_now_iso)
    request_id: str = ""

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "rule_id": self.rule_id,
            "reason": self.reason,
            "checked_at": self.checked_at,
            "request_id": self.request_id,
        }


__all__ = [
    "TerminalRequest",
    "TerminalQuery",
    "TerminalResult",
    "TerminalValidationResult",
]
