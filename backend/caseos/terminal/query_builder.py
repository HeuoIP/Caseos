"""Terminal Query Builder (Sprint 26.0-A, Terminal MVP V1).

Pure, deterministic transformation from a validated
``TerminalRequest`` to a ``TerminalQuery``.

Determinism rules (Sprint 26.0-A spec section 4):

    * ``query_text`` is the whitespace-joined, lowercased,
      trimmed concatenation of site_type, site_description, and
      user_requirements (in that order). Tokens that are missing
      or empty are skipped.
    * ``structured_constraints`` contains only KnowledgeObject
      field names that the existing RetrievalPipeline supports
      via ``RetrievalQuery.filters``. Concretely:

            site_type          -> filter on KO "site_type"
            preferred_theme    -> filter on KO "theme"     (when set)
            preferred_style    -> filter on KO "style"     (when set)
            age_range          -> filter on KO "interaction_type" or
                                  empty (age_range is informational
                                  in V1; see explanation below)

    * ``semantic_concepts`` is a tuple of strings: theme first,
      then style, then preferred_functions (each non-empty only).
      V1 does NOT call any semantic engine; the tuple is
      captured for forward compatibility.

    * ``limit`` is the contract default; the validator's T7 has
      already verified any caller-supplied limit.

The builder NEVER mutates the input request; it returns a fresh
``TerminalQuery``. Two calls with the same request produce the
same ``TerminalQuery`` up to ``query_id`` (auto-assigned and
unique per call; deterministic w.r.t. all other fields).
"""
from __future__ import annotations

from typing import Optional

from .contract import (
    DEFAULT_TERMINAL_CONTRACT,
    TerminalContract,
)
from .object import (
    TerminalQuery,
    TerminalRequest,
)


class TerminalQueryBuilderError(ValueError):
    """Raised when a request cannot be turned into a query."""


class TerminalQueryBuilder:
    """Deterministic Request -> Query mapper."""

    ENGINE_NAME: str = "TerminalQueryBuilder V1"

    def __init__(
        self,
        contract: Optional[TerminalContract] = None,
    ) -> None:
        if contract is None:
            contract = DEFAULT_TERMINAL_CONTRACT
        if not isinstance(contract, TerminalContract):
            raise TerminalQueryBuilderError(
                "contract must be a TerminalContract or None; got "
                + type(contract).__name__
            )
        self.contract: TerminalContract = contract

    # ---- public ----------------------------------------------------

    def build(self, request: TerminalRequest) -> TerminalQuery:
        if not isinstance(request, TerminalRequest):
            raise TerminalQueryBuilderError(
                "build() expects a TerminalRequest; got "
                + type(request).__name__
            )

        query_text = self._compose_query_text(request)
        constraints = self._compose_structured_constraints(request)
        concepts = self._compose_semantic_concepts(request)
        limit = self.contract.default_limit

        return TerminalQuery(
            query_text=query_text,
            structured_constraints=constraints,
            semantic_concepts=concepts,
            limit=limit,
        )

    def build_with_limit(
        self,
        request: TerminalRequest,
        limit: int,
    ) -> TerminalQuery:
        """Build a query with a caller-supplied Top-K.

        ``limit`` must be a positive int; the service / validator
        is responsible for clamping to ``contract.min_limit /
        contract.max_limit``.
        """
        if not isinstance(limit, int) or limit < 1:
            raise TerminalQueryBuilderError(
                "limit must be a positive int; got " + repr(limit)
            )
        clamped = self.contract.clamp_limit(limit)
        query_text = self._compose_query_text(request)
        constraints = self._compose_structured_constraints(request)
        concepts = self._compose_semantic_concepts(request)
        return TerminalQuery(
            query_text=query_text,
            structured_constraints=constraints,
            semantic_concepts=concepts,
            limit=clamped,
        )

    # ---- private helpers ------------------------------------------

    @staticmethod
    def _compose_query_text(request: TerminalRequest) -> str:
        parts: list = []
        if request.site_type:
            parts.append(request.site_type.strip())
        if request.site_description:
            parts.append(request.site_description.strip())
        if request.user_requirements:
            parts.append(request.user_requirements.strip())
        return " ".join(parts).lower().strip()

    @staticmethod
    def _compose_structured_constraints(
        request: TerminalRequest,
    ) -> tuple:
        out: list = []
        # site_type -> KO field "site_type"
        if request.site_type and request.site_type.strip():
            out.append(("site_type", request.site_type.strip()))
        # preferred_theme -> KO field "theme"
        if request.preferred_theme and request.preferred_theme.strip():
            out.append(("theme", request.preferred_theme.strip()))
        # preferred_style -> KO field "style"
        if request.preferred_style and request.preferred_style.strip():
            out.append(("style", request.preferred_style.strip()))
        return tuple(out)

    @staticmethod
    def _compose_semantic_concepts(
        request: TerminalRequest,
    ) -> tuple:
        out: list = []
        if request.preferred_theme and request.preferred_theme.strip():
            out.append(request.preferred_theme.strip())
        if request.preferred_style and request.preferred_style.strip():
            out.append(request.preferred_style.strip())
        for fn in request.preferred_functions:
            if fn and fn.strip():
                out.append(fn.strip())
        return tuple(out)


__all__ = [
    "TerminalQueryBuilderError",
    "TerminalQueryBuilder",
]
