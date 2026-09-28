"""Knowledge Retrieval Engine V1 (Sprint 24.0-A).

This module implements the **runtime engine** that consumes
a ``RetrievalQuery`` and produces a ``RetrievalResult``.
V1 ships only a deterministic, pure keyword matcher --
no LLM, no embedding, no vector DB.

Design:

    * ``KnowledgeRetrievalEngine`` is an abstract base class.
      Future sprints can add ``SemanticRetrievalEngine``
      (embedding) or other backends without changing the
      contract layer.

    * ``KeywordRetrievalEngine`` is the V1 implementation.
      It runs entirely on the textual content of each KO
      and on the caller's filters. Match scoring is
      deterministic: given the same inputs, every call
      produces the same ``RetrievalResult``.

Match modes:

    any     -- the KO passes if any query field matches.
    all     -- the KO passes only if every query field matches.
    exact   -- the entire ``query_text`` is contained verbatim
               in a single KO field, OR every (key, value) pair
               in ``filters`` matches the KO exactly.

Sort orders:

    score / knowledge_id / version / created_at
    asc / desc

The engine is a *reader* of Knowledge Objects. It never
mutates the records it consumes. KO snapshots inside
``RetrievalHit.knowledge_object_snapshot`` are deep-copied
on entry (via ``RetrievalHit.__post_init__``).

Architecture boundary (Sprint 24.0-A spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This module MAY import from:
        * caseos.knowledge.object   (KO schema)
        * caseos.knowledge.retrieval (sibling modules)
        * stdlib
"""
from __future__ import annotations

import abc
import re
import time
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

from caseos.knowledge.object.schema import REQUIRED_FIELDS as KO_REQUIRED_FIELDS

from .object import (
    DEFAULT_SORT_BY,
    DEFAULT_SORT_ORDER,
    RetrievalHit,
    RetrievalQuery,
    RetrievalResult,
)
from .schema import DEFAULT_QUERY_FIELDS
from .validator import RetrievalValidationResult, RetrievalValidator


# ---------------------------------------------------------------------------
# Tokenization helpers
# ---------------------------------------------------------------------------

# A small, explicit stopword set. The V1 keyword engine treats
# these as uninformative: matching them does not contribute to
# the score. Linguistic completeness is NOT the goal here.
_STOPWORDS: frozenset = frozenset(
    """
    a an the of in on at to for from with and or but if is are was
    were be been being do does did has have had this that these those
    it its as by about into over under between through during before
    after above below up down out off again further then once here there
    when where why how all any both each few more most other some such no
    nor not only own same so than too very s t can will just don should now
    """.split()
)


def _tokenize(text: Any) -> List[str]:
    """Lowercase + split a string into token list, ignoring
    non-alpha-numeric chars and stopwords. ``text`` that is
    not a string yields an empty token list."""
    if not isinstance(text, str):
        return []
    lowered = text.lower()
    tokens = re.findall(r"[a-z0-9_]+", lowered)
    return [t for t in tokens if t and t not in _STOPWORDS]


def _snippet_of(value: Any) -> str:
    """Best-effort short excerpt of an arbitrary value."""
    if isinstance(value, str):
        return value[:120]
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value)[:120]
    return str(value)[:120]


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------


class KnowledgeRetrievalEngine(abc.ABC):
    """The engine contract every backend must implement."""

    @abc.abstractmethod
    def execute(
        self,
        query: RetrievalQuery,
        knowledge_objects: Sequence[Any],
        *,
        binding_lookup: Optional[Mapping[str, Sequence[str]]] = None,
        required_attribute_lookup: Optional[
            Mapping[str, Mapping[str, Any]]
        ] = None,
    ) -> RetrievalResult:
        """Run a retrieval against ``knowledge_objects``."""


# ---------------------------------------------------------------------------
# KeywordRetrievalEngine V1
# ---------------------------------------------------------------------------


def _get_attr_safely(obj: Any, name: str, default: Any = None) -> Any:
    """Duck-typed attribute access (we read both dataclass KO
    and dict-shaped KO inputs)."""
    if obj is None:
        return default
    if hasattr(obj, name):
        return getattr(obj, name)
    if isinstance(obj, dict):
        return obj.get(name, default)
    return default


def _ko_to_dict(ko: Any) -> Dict[str, Any]:
    """Convert a KnowledgeObject instance or a dict into a flat
    dict with only ``KO_REQUIRED_FIELDS`` keys (plus any extra
    ``query_fields`` the caller named)."""
    out: Dict[str, Any] = {}
    for fname in KO_REQUIRED_FIELDS:
        out[fname] = _get_attr_safely(ko, fname)
    return out


def _matches_filters(ko: Dict[str, Any], filters: Mapping[str, Any]) -> bool:
    """Exact-match over filters. Every (key, value) pair must
    equal the KO's value."""
    for k, v in filters.items():
        if ko.get(k) != v:
            return False
    return True


def _has_required_attributes(
    ko: Any,
    required: Sequence[str],
    attribute_lookup: Optional[Mapping[str, Mapping[str, Any]]],
) -> bool:
    """A KO satisfies a ``required`` attribute when it has a
    non-empty value for that attribute. Two lookup modes:

    1. KO is the dataclass ``KnowledgeObject``: the attribute
       is satisfied when ``getattr(ko, name)`` returns a
       truthy value.
    2. ``attribute_lookup`` is provided (mapping from
       knowledge_id to dict of attribute values): the
       engine reads the named attribute from the lookup.
    """
    if not required:
        return True
    ko_id = _get_attr_safely(ko, "knowledge_id", "")
    for name in required:
        if attribute_lookup is not None and ko_id in attribute_lookup:
            value = attribute_lookup[ko_id].get(name)
        else:
            value = _get_attr_safely(ko, name)
        if value is None:
            return False
        if isinstance(value, (list, tuple)) and len(value) == 0:
            return False
        if isinstance(value, str) and not value.strip():
            return False
    return True


def _in_bound_domain(
    ko_id: str,
    bound_domain_ids: Sequence[str],
    binding_lookup: Optional[Mapping[str, Sequence[str]]],
) -> bool:
    """Skip-the-KO gate (Sprint 24.0-A hard filter).

    If ``bound_domain_ids`` is empty, the gate is open. If it
    is non-empty, the lookup must bind ``ko_id`` to at least
    one of the requested domain ids. When the lookup is
    missing for the KO, the KO is skipped (no implicit match).
    """
    if not bound_domain_ids:
        return True
    if not binding_lookup:
        return False
    ko_domains = binding_lookup.get(ko_id, ())
    return any(d in bound_domain_ids for d in ko_domains)


class KeywordRetrievalEngine(KnowledgeRetrievalEngine):
    """V1 retrieval engine -- pure, deterministic keyword match.

    Algorithm:

        For each KO in the input:
            * If KO lacks ``knowledge_id``: skip.
            * If bound_domain_ids is non-empty and no binding
              matches: skip.
            * Compute per-field match score against query_tokens.
            * Apply ``match_mode`` to decide whether the KO passes.
            * Apply ``filters`` (exact-match).
            * Apply ``required_attributes`` (non-empty).
            * Combined score = sum(field_score) / num_scanned.
            * If 0 < score <= 1: record a RetrievalHit.

        Sort hits by ``sort_by``/``sort_order`` and apply ``limit``.
    """

    def __init__(
        self,
        *,
        max_snippet_length: int = 120,
        field_token_weight_cap: int = 1,
    ) -> None:
        self.max_snippet_length = int(max_snippet_length)
        self.field_token_weight_cap = int(field_token_weight_cap)

    # ---- public ----------------------------------------------------

    def execute(
        self,
        query: RetrievalQuery,
        knowledge_objects: Sequence[Any],
        *,
        binding_lookup: Optional[Mapping[str, Sequence[str]]] = None,
        required_attribute_lookup: Optional[
            Mapping[str, Mapping[str, Any]]
        ] = None,
    ) -> RetrievalResult:
        """Execute the retrieval. Returns a (frozen) RetrievalResult.

        Pre-condition: the caller may have validated the query
        with ``RetrievalValidator``. The engine still re-runs
        Q7 (you must ask for something) and otherwise treats an
        invalid query as a zero-hit result.
        """
        started = time.perf_counter()

        # ---- guard: invalid query ---------------------------------
        validator = RetrievalValidator()
        vresult: RetrievalValidationResult = validator.validate(query)
        if not vresult.valid:
            return RetrievalResult(
                query_id=getattr(query, "query_id", ""),
                success=False,
                total_hits=0,
                hits=(),
                execution_time_ms=(time.perf_counter() - started) * 1000.0,
            )

        # ---- inputs ------------------------------------------------
        query_tokens: List[str] = _tokenize(
            getattr(query, "query_text", "")
        )
        # Filter dedupe, keep caller order.
        seen = set()
        qfields: List[str] = []
        for f in getattr(query, "query_fields", ()) or DEFAULT_QUERY_FIELDS:
            if f and f not in seen:
                seen.add(f)
                qfields.append(f)
        if not qfields:
            qfields = list(DEFAULT_QUERY_FIELDS)

        filters = dict(getattr(query, "filters", {}) or {})
        bound_domain_ids = list(
            getattr(query, "bound_domain_ids", ()) or []
        )
        required_attrs = list(
            getattr(query, "required_attributes", ()) or []
        )
        match_mode = getattr(query, "match_mode", "any")
        sort_by = getattr(query, "sort_by", DEFAULT_SORT_BY)
        sort_order = getattr(query, "sort_order", DEFAULT_SORT_ORDER)
        limit = int(getattr(query, "limit", 20))

        # ---- per-KO scoring ---------------------------------------
        candidates: List[RetrievalHit] = []
        for ko in knowledge_objects:
            ko_id = _get_attr_safely(ko, "knowledge_id", "")
            if not ko_id:
                continue

            # Domain-bound gate.
            if not _in_bound_domain(
                ko_id, bound_domain_ids, binding_lookup
            ):
                continue

            # Filters.
            ko_dict = _ko_to_dict(ko)
            if filters and not _matches_filters(ko_dict, filters):
                continue

            # Required attributes.
            if not _has_required_attributes(
                ko, required_attrs, required_attribute_lookup
            ):
                continue

            # Per-field score.
            matched_fields: List[str] = []
            matched_snippets: Dict[str, str] = {}
            per_field_hits: List[float] = []
            for field_name in qfields:
                value = _get_attr_safely(ko, field_name)
                tokenized_value_tokens = _tokenize(value)
                if not tokenized_value_tokens:
                    continue
                value_token_set = set(tokenized_value_tokens)
                hits_in_field = sum(
                    1 for t in query_tokens if t in value_token_set
                )
                if hits_in_field == 0:
                    continue
                # Per-field normalized score.
                per_field = min(
                    hits_in_field / max(len(query_tokens), 1), 1.0
                )
                per_field_hits.append(per_field)
                matched_fields.append(field_name)
                matched_snippets[field_name] = _snippet_of(value)

            # Apply match_mode gate.
            if match_mode == "any":
                field_match_pass = len(matched_fields) > 0
            elif match_mode == "all":
                field_match_pass = len(matched_fields) >= len(qfields)
            else:  # "exact"
                if query_tokens:
                    all_text = " ".join(
                        str(_get_attr_safely(ko, fn, "")) for fn in qfields
                    )
                    lowered = all_text.lower()
                    field_match_pass = (
                        getattr(query, "query_text", "").strip().lower()
                        in lowered
                    )
                else:
                    field_match_pass = False

            if not field_match_pass:
                continue

            if not per_field_hits:
                continue

            # Combined score: cap number of contributing fields
            # so a single field cannot dominate the ranking.
            weighted = sum(
                min(s, self.field_token_weight_cap)
                for s in per_field_hits
            )
            combined = weighted / max(len(qfields), 1)
            if combined > 1.0:
                combined = 1.0
            if combined < 0.0:
                combined = 0.0

            knowledge_version = int(
                _get_attr_safely(ko, "version", 1) or 1
            )
            snapshot = {
                k: ko_dict.get(k) for k in KO_REQUIRED_FIELDS if k != "image_refs"
            }
            candidates.append(
                RetrievalHit(
                    knowledge_id=ko_id,
                    knowledge_version=knowledge_version,
                    match_score=combined,
                    matched_fields=list(matched_fields),
                    matched_snippets=dict(matched_snippets),
                    knowledge_object_snapshot=snapshot,
                )
            )

        # ---- sort --------------------------------------------------
        candidates = _sort_hits(
            candidates, sort_by=sort_by, sort_order=sort_order
        )

        # ---- limit -------------------------------------------------
        hits = tuple(candidates[:limit])

        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return RetrievalResult(
            query_id=getattr(query, "query_id", ""),
            success=True,
            total_hits=len(hits),
            hits=hits,
            execution_time_ms=elapsed_ms,
        )


# ---------------------------------------------------------------------------
# Sort helpers
# ---------------------------------------------------------------------------


def _sort_hits(
    hits: List[RetrievalHit], *, sort_by: str, sort_order: str
) -> List[RetrievalHit]:
    if not hits:
        return hits
    reverse = sort_order == "desc"

    if sort_by == "score":
        key_fn: Callable[[RetrievalHit], Any] = (
            lambda h: h.match_score
        )
    elif sort_by == "knowledge_id":
        key_fn = lambda h: h.knowledge_id
    elif sort_by == "version":
        key_fn = lambda h: h.knowledge_version
    elif sort_by == "created_at":
        key_fn = lambda h: h.knowledge_object_snapshot.get(
            "created_at", ""
        )
    else:
        key_fn = lambda h: h.match_score

    return sorted(hits, key=key_fn, reverse=reverse)


__all__ = [
    "KnowledgeRetrievalEngine",
    "KeywordRetrievalEngine",
    "_tokenize",
    "_STOPWORDS",
]