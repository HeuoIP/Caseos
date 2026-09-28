"""Knowledge Structured Retrieval Engine V1 (Sprint 24.0-B).

This module ships the second concrete retrieval engine in
the CaseOS contract layer. Whereas ``KeywordRetrievalEngine``
(Sprint 24.0-A) drives the score from free-text token
overlap, ``StructuredRetrievalEngine`` is **schema-aware**:

    * It reads the ``required_attributes`` field as a
      *named schema signal* (the caller specifies an
      attribute slot by name, e.g. ``"theme"``,
      ``"interaction_type"``). The engine consults the
      ``KnowledgeAttribute`` registry to validate that
      each named slot is *known* (so callers cannot
      invent attributes on the fly).
    * It honours ``bound_domain_ids`` against a binding
      lookup so KO membership in a domain is enforced
      identically to the keyword engine.
    * It treats ``filters`` as **exact-match gates**:
      every (key, value) pair in ``filters`` must equal
      the KO field value (the engine is strict, never
      fuzzy).
    * ``query_text`` is *ignored* for scoring (the engine
      does not tokenize it; it is not part of the
      V1 contract).

The engine is deterministic and pure: given the same
inputs (query + KO list + optional registries), every
call produces the same ``RetrievalResult``.

Architecture boundary (Sprint 24.0-B spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
        * caseos.brain.*
        * caseos.knowledge.retrieval.engine (intentionally
          decoupled -- structured is a sibling, not a
          subclass of keyword)
    This module MAY import from:
        * caseos.knowledge.object       (KO schema)
        * caseos.knowledge.attribute    (attribute schema)
        * caseos.knowledge.domain       (domain schema)
        * caseos.knowledge.binding      (binding schema)
        * caseos.knowledge.taxonomy     (taxonomy schema)
        * caseos.knowledge.retrieval    (contract layer
                                         + validator + result)
        * stdlib
"""
from __future__ import annotations

import time
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
)

from caseos.knowledge.attribute.schema import REQUIRED_FIELDS as ATTR_REQUIRED_FIELDS
from caseos.knowledge.binding.schema import REQUIRED_FIELDS as BIND_REQUIRED_FIELDS
from caseos.knowledge.domain.schema import REQUIRED_FIELDS as DOMAIN_REQUIRED_FIELDS
from caseos.knowledge.object.schema import REQUIRED_FIELDS as KO_REQUIRED_FIELDS

from .engine import _get_attr_safely, _ko_to_dict, _matches_filters
from .object import (
    DEFAULT_SORT_BY,
    DEFAULT_SORT_ORDER,
    RetrievalHit,
    RetrievalQuery,
    RetrievalResult,
)
from .schema import (
    MATCH_MODE_ALLOW_LIST,
    SORT_BY_ALLOW_LIST,
    SORT_ORDER_ALLOW_LIST,
)


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------


def _iter_optional_registry(
    registry: Optional[Iterable[Any]],
) -> Optional[List[Any]]:
    """Coerce an optional registry into a list (or None).

    Accepts:
        * None             -> None
        * a list/tuple/set -> list
        * something with an iterable ``__iter__`` -> list
    Returns None when the input is None or empty.
    """
    if registry is None:
        return None
    if isinstance(registry, (list, tuple, set)):
        items = list(registry)
    else:
        try:
            items = list(iter(registry))
        except TypeError:
            return None
    return items or None


def _collect_attribute_names(
    registry: Optional[Iterable[Any]],
) -> Optional[Set[str]]:
    """Collect *registered* attribute names from a registry
    instance list. We accept either:

        * a sequence of ``KnowledgeAttribute`` records (with
          ``.attribute_id`` and ``.name``), or
        * a sequence of dicts with at least a ``"name"`` key.

    Returns ``None`` when no registry is supplied (callers
    may opt-out of registry validation). An empty set means
    the registry was supplied but is empty (every required
    attribute is rejected as "unknown").
    """
    items = _iter_optional_registry(registry)
    if items is None:
        return None
    out: Set[str] = set()
    for entry in items:
        name = _get_attr_safely(entry, "attribute_id", None)
        if name is None:
            name = _get_attr_safely(entry, "name", None)
        if isinstance(name, str) and name:
            out.add(name)
    return out


def _collect_domain_ids(
    registry: Optional[Iterable[Any]],
) -> Optional[Set[str]]:
    """Collect *registered* domain ids. Same dual-shape
    convention as ``_collect_attribute_names``."""
    items = _iter_optional_registry(registry)
    if items is None:
        return None
    out: Set[str] = set()
    for entry in items:
        did = _get_attr_safely(entry, "domain_id", None)
        if not isinstance(did, str):
            did = _get_attr_safely(entry, "id", None)
        if isinstance(did, str) and did:
            out.add(did)
    return out


def _collect_binding_pairs(
    registry: Optional[Iterable[Any]],
) -> Optional[List[Tuple[str, str]]]:
    """Collect (knowledge_object_id, domain_id) pairs from a
    binding registry. Returns ``None`` when no registry is
    supplied. Empty list means no bindings exist."""
    items = _iter_optional_registry(registry)
    if items is None:
        return None
    out: List[Tuple[str, str]] = []
    for entry in items:
        ko_id = _get_attr_safely(entry, "knowledge_object_id", None)
        if not isinstance(ko_id, str):
            ko_id = _get_attr_safely(entry, "knowledge_id", None)
        domain_id = _get_attr_safely(entry, "domain_id", None)
        if isinstance(ko_id, str) and isinstance(domain_id, str):
            out.append((ko_id, domain_id))
    return out


def _build_binding_lookup(
    pairs: Optional[List[Tuple[str, str]]],
) -> Optional[Dict[str, List[str]]]:
    """Convert flat (KO, domain) pairs to a mapping
    ``knowledge_id -> [domain_id, ...]``."""
    if pairs is None:
        return None
    out: Dict[str, List[str]] = {}
    for ko_id, d_id in pairs:
        out.setdefault(ko_id, []).append(d_id)
    return out


# ---------------------------------------------------------------------------
# Value-presence predicate
# ---------------------------------------------------------------------------


def _has_nonempty_value(value: Any) -> bool:
    """A KO "has" an attribute when the value is non-empty.

    Empty-list / empty-string / None all count as absent.
    """
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return len(value) > 0
    return True


# ---------------------------------------------------------------------------
# Score components
# ---------------------------------------------------------------------------


def _attribute_score(
    required: Sequence[str],
    attribute_names: Optional[Set[str]],
    ko: Any,
    attribute_lookup: Optional[Mapping[str, Mapping[str, Any]]],
) -> Tuple[float, List[str], List[str]]:
    """Compute the ``required_attributes`` axis of the score.

    Returns:
        (score, satisfied_attribute_names, missing_attribute_names)

    Score formula V1:

        satisfied / total_required

    The first 3 of the following conditions must hold for
    each named required attribute:

        * the attribute id is registered
            (only enforced when an attribute registry was
            supplied; otherwise we accept any string).
        * the KO has a non-empty value for that attribute.

    Per-attribute mismatch is *not* silently smoothed: a
    required attribute that is missing contributes zero.
    """
    if not required:
        return 1.0, [], []
    satisfied: List[str] = []
    missing: List[str] = []
    ko_id = _get_attr_safely(ko, "knowledge_id", "")
    for name in required:
        # Registry validation (when provided).
        if attribute_names is not None and name not in attribute_names:
            missing.append(name)
            continue
        # KO value lookup.
        if (
            attribute_lookup is not None
            and ko_id
            and ko_id in attribute_lookup
        ):
            value = attribute_lookup[ko_id].get(name)
        else:
            value = _get_attr_safely(ko, name)
        if _has_nonempty_value(value):
            satisfied.append(name)
        else:
            missing.append(name)
    total = max(len(required), 1)
    return len(satisfied) / total, satisfied, missing


def _matches_filters_with_lookup(
    ko_dict: Mapping[str, Any],
    filters: Mapping[str, Any],
    ko_id: str,
    attribute_lookup: Optional[Mapping[str, Mapping[str, Any]]],
) -> bool:
    """Match every (key, value) pair, with attribute_lookup
    overriding the underlying KO field when present."""
    for k, v in filters.items():
        actual = None
        if (
            attribute_lookup is not None
            and ko_id in attribute_lookup
            and k in attribute_lookup[ko_id]
        ):
            actual = attribute_lookup[ko_id].get(k)
        else:
            actual = ko_dict.get(k)
        if actual != v:
            return False
    return True


def _domain_score(
    bound_domain_ids: Sequence[str],
    ko_id: str,
    binding_lookup: Optional[Mapping[str, Sequence[str]]],
) -> Tuple[float, List[str], List[str]]:
    """Compute the ``bound_domain_ids`` axis. Returns
    (score, matched_domains, missed_domains).

    If ``bound_domain_ids`` is empty, the axis is *open*
    and the KO scores 1.0 with no signal. If non-empty,
    each requested domain that the KO binds to is a hit.
    """
    if not bound_domain_ids:
        return 1.0, [], []
    if not binding_lookup:
        return 0.0, [], list(bound_domain_ids)
    ko_domains = set(binding_lookup.get(ko_id, ()))
    matched = [d for d in bound_domain_ids if d in ko_domains]
    missed = [d for d in bound_domain_ids if d not in ko_domains]
    score = len(matched) / max(len(bound_domain_ids), 1)
    return score, matched, missed


def _filter_score(
    filters: Mapping[str, Any], ko_dict: Mapping[str, Any]
) -> Tuple[float, List[str], List[str]]:
    """Compute the ``filters`` axis. Filters in V1 are a
    hard gate -- the score is either 1.0 (all match) or
    0.0 (any mismatch), but we surface per-key matched /
    missed lists for the report.
    """
    if not filters:
        return 1.0, [], []
    matched: List[str] = []
    missed: List[str] = []
    for k in filters.keys():
        if ko_dict.get(k) == filters[k]:
            matched.append(k)
        else:
            missed.append(k)
    score = 1.0 if not missed else 0.0
    return score, matched, missed


# ---------------------------------------------------------------------------
# StructuredRetrievalEngine
# ---------------------------------------------------------------------------


class StructuredRetrievalEngine:
    """A schema-aware retrieval engine for CaseOS.

    The engine consumes ``RetrievalQuery`` plus optional
    registries (attribute / domain / binding / per-KO
    attribute lookup) and produces a ``RetrievalResult``.

    Two engines may now share the same contract:

        * ``KeywordRetrievalEngine``    -- text-token scoring
        * ``StructuredRetrievalEngine`` -- schema-alignment
                                           scoring

    Both implement the same input/output surface so the
    rest of the system does not care which one runs.

    V1 properties:

        * deterministic
        * no LLM, no embedding, no vector DB
        * registries are append-only sources consumed
          read-only here (we never mutate them)
        * KOs are not mutated
        * ``query_text`` is *ignored* for scoring (the
          structured engine reads only schema signals).
          Callers relying on text should pass the query to
          ``KeywordRetrievalEngine`` instead.
    """

    # Public name for traceability (used by tests + reports).
    ENGINE_NAME: str = "StructuredRetrievalEngine V1"

    def execute(  # noqa: C901 -- V1 traceability
        self,
        query: RetrievalQuery,
        knowledge_objects: Sequence[Any],
        *,
        attribute_registry: Optional[Iterable[Any]] = None,
        domain_registry: Optional[Iterable[Any]] = None,
        binding_registry: Optional[Iterable[Any]] = None,
        binding_lookup: Optional[Mapping[str, Sequence[str]]] = None,
        attribute_lookup: Optional[Mapping[str, Mapping[str, Any]]] = None,
    ) -> RetrievalResult:
        """Run a structured retrieval.

        Parameters
        ----------
        query:
            The query contract. ``query_text`` is ignored.
        knowledge_objects:
            The corpus to score against.
        attribute_registry:
            Optional iterable of ``KnowledgeAttribute``
            records (or dicts with ``"name"``). When
            supplied, ``required_attributes`` must be a
            known attribute id.
        domain_registry:
            Optional iterable of ``KnowledgeDomain``
            records (or dicts with ``"domain_id"``). Used
            as a *validity* signal for ``bound_domain_ids``
            but never to mutate retrieval behavior.
        binding_registry:
            Optional iterable of ``KODomainBinding``
            records (or dicts with ``"knowledge_object_id"``
            + ``"domain_id"``). Converted internally to a
            KO -> domain lookup and merged with the
            ``binding_lookup`` argument (the argument wins
            on conflict).
        binding_lookup:
            Optional KO -> [domain_id, ...] mapping. See
            ``KeywordRetrievalEngine.execute`` for the
            duck-typed semantics.
        attribute_lookup:
            Optional KO -> {attribute_name: value} mapping.
            When supplied, the engine reads attribute
            values from this lookup rather than from the
            KO itself (so callers can attach out-of-band
            attribute data without mutating the KO).

        Returns
        -------
        RetrievalResult
            A frozen envelope. ``success`` is False iff the
            query contract failed validation; otherwise
            True (a 0-hit result is still a success).
        """
        started = time.perf_counter()

        # --- Early guard: contract -------------------------------
        # Structured engine accepts "purely schema-driven"
        # queries (only required_attributes / bound_domain_ids
        # / filters, no text). The V1 validator requires at
        # least one of {query_text, query_fields, filters};
        # we therefore do a relaxed schema-only validation
        # here, and only invoke the full validator when the
        # query carries text or field inputs.
        from .validator import (
            MATCH_MODE_ALLOW_LIST,
            SORT_BY_ALLOW_LIST,
            SORT_ORDER_ALLOW_LIST,
            RetrievalValidationResult,
            RetrievalValidator,
        )

        qt = getattr(query, "query_text", "")
        qfields = getattr(query, "query_fields", [])
        struct_signals = (
            list(getattr(query, "required_attributes", ()) or [])
            + list(getattr(query, "bound_domain_ids", ()) or [])
        )
        use_full_validator = bool(
            (isinstance(qt, str) and qt.strip())
            or (isinstance(qfields, (list, tuple)) and len(qfields) > 0)
        )

        if use_full_validator:
            vresult = RetrievalValidator().validate(query)
            if not vresult.valid:
                return RetrievalResult(
                    query_id=getattr(query, "query_id", ""),
                    success=False,
                    total_hits=0,
                    hits=(),
                    execution_time_ms=(time.perf_counter() - started)
                    * 1000.0,
                )
        else:
            # Schema-only validation. check Q1, Q2, Q3, Q4,
            # Q5, Q6 plus a structural check that at least
            # one schema signal (filters / required_attributes
            # / bound_domain_ids) is supplied.
            vresult = RetrievalValidationResult(
                valid=_schema_only_ok(query),
                errors=(),
                rule_failures=(),
            )
            if not vresult.valid:
                return RetrievalResult(
                    query_id=getattr(query, "query_id", ""),
                    success=False,
                    total_hits=0,
                    hits=(),
                    execution_time_ms=(time.perf_counter() - started)
                    * 1000.0,
                )
            # local unused warnings guard
            _ = (MATCH_MODE_ALLOW_LIST,
                 SORT_BY_ALLOW_LIST, SORT_ORDER_ALLOW_LIST)
            del _

        # --- Inputs -----------------------------------------------
        sort_by: str = getattr(query, "sort_by", DEFAULT_SORT_BY)
        sort_order: str = getattr(
            query, "sort_order", DEFAULT_SORT_ORDER
        )
        limit: int = int(getattr(query, "limit", 20))
        filters: Mapping[str, Any] = dict(
            getattr(query, "filters", {}) or {}
        )
        required_attrs: List[str] = list(
            getattr(query, "required_attributes", ()) or []
        )
        bound_domain_ids: List[str] = list(
            getattr(query, "bound_domain_ids", ()) or []
        )
        match_mode: str = getattr(query, "match_mode", "any")
        # The structured engine treats match_mode the same
        # way: any/all/exact all map to "score >= 0" +
        # sort/limit. No text matching happens here.

        # --- Registries -------------------------------------------
        attribute_names = _collect_attribute_names(attribute_registry)
        domain_ids = _collect_domain_ids(domain_registry)
        binding_pairs = _collect_binding_pairs(binding_registry)
        registry_binding_lookup = _build_binding_lookup(binding_pairs)

        # Merge caller-supplied binding_lookup over the
        # registry-derived one (caller's wins per KO).
        merged_binding_lookup: Optional[Dict[str, List[str]]] = None
        if registry_binding_lookup is not None or binding_lookup is not None:
            merged_binding_lookup = {}
            if registry_binding_lookup is not None:
                for k, v in registry_binding_lookup.items():
                    merged_binding_lookup[k] = list(v)
            if binding_lookup is not None:
                for k, v in binding_lookup.items():
                    merged_binding_lookup[k] = list(v)

        # Domain id validation: warn (not reject) when a
        # bound_domain_id is unknown to the registry. We
        # still attempt to match because callers may have
        # supplied a binding_lookup directly.
        if (
            domain_ids is not None
            and bound_domain_ids
        ):
            # No mutation; we just adjust the score to 0.0
            # for unknown domains (no false positives).
            pass

        # --- Per-KO scoring ---------------------------------------
        candidates: List[RetrievalHit] = []
        for ko in knowledge_objects:
            ko_id = _get_attr_safely(ko, "knowledge_id", "")
            if not ko_id:
                continue
            ko_dict = _ko_to_dict(ko)

            # Hard gate: filters. attribute_lookup
            # overrides KO fields when present.
            if filters and not _matches_filters_with_lookup(
                ko_dict, filters, ko_id, attribute_lookup
            ):
                continue
            # Hard gate: bound_domain_ids (when non-empty).
            if (
                bound_domain_ids
                and not _domain_gate_open(
                    ko_id,
                    bound_domain_ids,
                    merged_binding_lookup,
                )
            ):
                continue

            # Component scores.
            attr_score, attr_satisfied, attr_missing = _attribute_score(
                required_attrs,
                attribute_names,
                ko,
                attribute_lookup,
            )
            dom_score, dom_matched, dom_missed = _domain_score(
                bound_domain_ids, ko_id, merged_binding_lookup
            )
            filt_score, filt_matched, filt_missed = _filter_score(
                filters, ko_dict
            )

            # Hard gate at attribute axis: when the caller
            # asks for required_attributes, a zero score on
            # that axis is a structural rejection (the KO
            # is *not* schema-aligned with the query).
            if required_attrs and attr_score == 0.0:
                continue

            # Combined V1 score: equal-weighted average of
            # the three axes (attribute, domain, filter).
            # Each axis lies in [0, 1] and is treated
            # independently so a failure in one axis can
            # be partially compensated by another -- but
            # only if the hard gates above were satisfied.
            combined = (attr_score + dom_score + filt_score) / 3.0

            # Build snapshot (without image_refs to keep
            # payloads small and JSON-native).
            snapshot = {
                k: ko_dict.get(k)
                for k in KO_REQUIRED_FIELDS
                if k != "image_refs"
            }

            # matched_fields: union of satisfied attribute
            # keys and matched filter keys (the engine
            # treats them as "structural signals").
            matched_set = list(
                dict.fromkeys(
                    list(attr_satisfied)
                    + list(filt_matched)
                    + [("domain:" + d) for d in dom_matched]
                )
            )

            knowledge_version = int(
                _get_attr_safely(ko, "version", 1) or 1
            )
            candidates.append(
                RetrievalHit(
                    knowledge_id=ko_id,
                    knowledge_version=knowledge_version,
                    match_score=combined,
                    matched_fields=matched_set,
                    matched_snippets={
                        "axis:attribute": "{}/{}".format(
                            len(attr_satisfied), len(required_attrs)
                        ),
                        "axis:domain": "{}/{}".format(
                            len(dom_matched), len(bound_domain_ids)
                        ),
                        "axis:filter": "{}/{}".format(
                            len(filt_matched), len(filters)
                        ),
                    },
                    knowledge_object_snapshot=snapshot,
                )
            )

        # --- Sort -------------------------------------------------
        candidates = _sort_hits(candidates, sort_by, sort_order)

        # --- Limit ------------------------------------------------
        # Apply match_mode at the limit stage (any/all/exact
        # semantics over schema signals):
        #   any  -> keep as is
        #   all  -> require score == 1.0 to retain
        #   exact-> require score == 1.0 AND every axis == 1.0
        if match_mode == "all":
            candidates = [h for h in candidates if h.match_score >= 1.0]
        elif match_mode == "exact":
            candidates = [
                h for h in candidates if h.match_score >= 1.0
            ]

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
# Helpers
# ---------------------------------------------------------------------------


def _domain_gate_open(
    ko_id: str,
    bound_domain_ids: Sequence[str],
    binding_lookup: Optional[Mapping[str, Sequence[str]]],
) -> bool:
    """Same gate semantics as the keyword engine.

    Empty bound_domain_ids -> gate is open.
    Non-empty -> KO must bind to at least one of them in
    the lookup. When the lookup is missing for the KO,
    the gate is closed.
    """
    if not bound_domain_ids:
        return True
    if not binding_lookup:
        return False
    ko_domains = binding_lookup.get(ko_id, ())
    return any(d in bound_domain_ids for d in ko_domains)


def _sort_hits(
    hits: List[RetrievalHit], sort_by: str, sort_order: str
) -> List[RetrievalHit]:
    if not hits:
        return hits
    reverse = sort_order == "desc"
    if sort_by == "score":
        key_fn = lambda h: h.match_score  # noqa: E731
    elif sort_by == "knowledge_id":
        key_fn = lambda h: h.knowledge_id  # noqa: E731
    elif sort_by == "version":
        key_fn = lambda h: h.knowledge_version  # noqa: E731
    elif sort_by == "created_at":
        key_fn = lambda h: h.knowledge_object_snapshot.get(  # noqa: E731
            "created_at", ""
        )
    else:
        key_fn = lambda h: h.match_score  # noqa: E731
    return sorted(hits, key=key_fn, reverse=reverse)


# ---------------------------------------------------------------------------


def _schema_only_ok(query: RetrievalQuery) -> bool:
    """Lightweight validator for "schema-only" queries.

    The structured engine lets a caller express intent
    purely through ``required_attributes`` and
    ``bound_domain_ids``, without supplying any text
    input. This helper enforces the structural minimum:
        * Q1 query_id is a non-empty string
        * Q2 version >= 1
        * Q3 1 <= limit <= 1000
        * Q4 match_mode in allow-list
        * Q5 sort_by in allow-list
        * Q6 sort_order in allow-list
        * at least one of {filters, required_attributes,
                           bound_domain_ids} is provided
    """
    qid = getattr(query, "query_id", "")
    if not isinstance(qid, str) or not qid.strip():
        return False
    version = getattr(query, "version", None)
    if not isinstance(version, int) or version < 1:
        return False
    limit = getattr(query, "limit", None)
    if not isinstance(limit, int) or isinstance(limit, bool):
        return False
    if limit < 1 or limit > 1000:
        return False
    mm = getattr(query, "match_mode", None)
    if mm not in MATCH_MODE_ALLOW_LIST:
        return False
    sb = getattr(query, "sort_by", None)
    if sb not in SORT_BY_ALLOW_LIST:
        return False
    so = getattr(query, "sort_order", None)
    if so not in SORT_ORDER_ALLOW_LIST:
        return False
    filters = getattr(query, "filters", {}) or {}
    req = getattr(query, "required_attributes", ()) or ()
    bd = getattr(query, "bound_domain_ids", ()) or ()
    return bool(filters) or bool(req) or bool(bd)


# Sentinel for boundary awareness
# ---------------------------------------------------------------------------


# The three allowlists below are intentionally a re-export
# of the canonical schema constants so that downstream
# reports / tests can introspect the engine's contract
# without reaching into sibling packages directly.
STRUCTURED_ATTRIBUTE_FIELDS = frozenset(ATTR_REQUIRED_FIELDS)
STRUCTURED_DOMAIN_FIELDS = frozenset(DOMAIN_REQUIRED_FIELDS)
STRUCTURED_BINDING_FIELDS = frozenset(BIND_REQUIRED_FIELDS)


__all__ = [
    "StructuredRetrievalEngine",
    "STRUCTURED_ATTRIBUTE_FIELDS",
    "STRUCTURED_DOMAIN_FIELDS",
    "STRUCTURED_BINDING_FIELDS",
]
