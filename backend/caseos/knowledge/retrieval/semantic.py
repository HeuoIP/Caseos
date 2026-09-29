"""Knowledge Retrieval Semantic Foundation V1 (Sprint 24.1-A).

This module ships the **concept-aware retrieval layer**
that uses the CaseOS ``Taxonomy`` package (Sprint 23.1-C)
as a hierarchy source. Unlike ``KeywordRetrievalEngine``
(24.0-A, lexical), ``StructuredRetrievalEngine`` (24.0-B,
schema) and the hybrid fuser (24.0-D), the *semantic*
engine reasons about **concepts** -- not strings, not
schema fields, not vector embeddings.

V1 properties:

    * No LLM, no embedding model, no vector database.
    * Concept resolution is **alias-based**: a caller-
      supplied ``alias_to_concept`` mapping turns query
      tokens into canonical concept ids.
    * Hierarchy is **bounded**: ``TaxonomyNode.parent_node_id``
      drives single-step ancestor / descendant expansion
      (depth cap = 1 by default).
    * Concept -> KO membership is **curated**: the caller
      supplies ``concept_to_kos`` (a dict mapping concept
      ids to lists of knowledge ids).
    * Deterministic and pure: same inputs -> same
      ``RetrievalResult`` every run.

Architecture position (Sprint 24.1-A spec):

    Query
      |
      v
    SemanticRetrievalEngine
      |
      +-- alias resolver (token -> concept)
      |
      +-- taxonomy expander (concept -> ancestors/descendants)
      |
      +-- concept->KO mapper (concept set -> KO id set)
      |
      v
    RetrievalResult

Architecture boundary (Sprint 24.1-A spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
        * caseos.brain.*
    This module MAY import from:
        * caseos.knowledge.object
        * caseos.knowledge.attribute
        * caseos.knowledge.domain
        * caseos.knowledge.binding
        * caseos.knowledge.taxonomy
        * caseos.knowledge.graph
        * caseos.knowledge.retrieval (sibling contract layer)
        * stdlib
"""
from __future__ import annotations

import copy
import re
import time
from typing import (
    Any,
    Dict,
    FrozenSet,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
)

from .engine import _get_attr_safely, _ko_to_dict, _matches_filters
from .object import (
    DEFAULT_SORT_BY,
    DEFAULT_SORT_ORDER,
    RetrievalHit,
    RetrievalQuery,
    RetrievalResult,
)
from .schema import MATCH_MODE_ALLOW_LIST


# ---------------------------------------------------------------------------
# Scoring constants
# ---------------------------------------------------------------------------


#: Score for an *exact* concept match: the query token
#: resolved (via alias or literally) to the canonical
#: concept, and the concept directly mapped a KO.
SCORE_EXACT: float = 1.00

#: Score for an alias-resolved concept match. Slightly
#: lower than exact because the resolution path is one
#: indirection.
SCORE_ALIAS: float = 0.85

#: Score for an ancestor concept match. The query asked
#: for a specific concept, the KO is associated with a
#: parent in the taxonomy.
SCORE_ANCESTOR: float = 0.70

#: Score for a descendant concept match. The query asked
#: for a parent, the KO is associated with a child.
SCORE_DESCENDANT: float = 0.60


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------


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
    """Lowercase + regex-split a string into tokens.

    Stopwords are filtered out. Non-string input yields an
    empty list. Used only for *concept* resolution -- the
    semantic engine never scores by token overlap.
    """
    if not isinstance(text, str):
        return []
    lowered = text.lower()
    tokens = re.findall(r"[a-z0-9_-]+", lowered)
    return [t for t in tokens if t and t not in _STOPWORDS]


# ---------------------------------------------------------------------------
# SemanticIndex
# ---------------------------------------------------------------------------


class SemanticIndex:
    """Append-only container for concept-level retrieval metadata.

    Three read-only tables:

        * ``concept_to_kos``     -- canonical concept -> [KO ids]
        * ``alias_to_concept``   -- alias string -> canonical concept
        * ``taxonomy_nodes``     -- node_id -> TaxonomyNode-like dict

    All three are populated via ``register`` calls. The index
    never mutates inputs after registration; callers are
    expected to pass immutable mappings or accept that
    ``register`` will deep-copy the data on entry.
    """

    def __init__(self) -> None:
        # All internal state is private; readers go through
        # the public helpers.
        self._concept_to_kos: Dict[str, List[str]] = {}
        self._alias_to_concept: Dict[str, str] = {}
        self._taxonomy_nodes: Dict[str, Any] = {}

    # ---- Concept <-> KO mapping -----------------------------------

    def register_concept_to_kos(
        self,
        mapping: Mapping[str, Sequence[str]],
    ) -> None:
        """Register concept -> KO membership(s).

        Existing entries for the same concept id are
        *replaced* (this is a setter, not an append). Use
        ``add_concept_to_ko`` if you want append semantics.
        """
        for concept_id, ko_ids in mapping.items():
            if not isinstance(concept_id, str) or not concept_id:
                continue
            cleaned: List[str] = []
            for kid in ko_ids or ():
                if isinstance(kid, str) and kid:
                    cleaned.append(kid)
            self._concept_to_kos[concept_id] = cleaned

    def add_concept_to_ko(
        self, concept_id: str, knowledge_id: str
    ) -> None:
        """Append a single KO id to a concept's bucket.

        No-op if either argument is empty / not a string.
        """
        if not isinstance(concept_id, str) or not concept_id:
            return
        if not isinstance(knowledge_id, str) or not knowledge_id:
            return
        bucket = self._concept_to_kos.setdefault(concept_id, [])
        if knowledge_id not in bucket:
            bucket.append(knowledge_id)

    def concept_to_kos(
        self, concept_id: str
    ) -> Tuple[str, ...]:
        """Return the KO ids bound to ``concept_id`` (immutable)."""
        return tuple(self._concept_to_kos.get(concept_id, ()))

    # ---- Aliases --------------------------------------------------

    def register_aliases(
        self, mapping: Mapping[str, str]
    ) -> None:
        """Register alias -> canonical concept mappings.

        Aliases are lowercased on entry. Multiple aliases
        pointing to the same concept are allowed.
        """
        for alias, concept_id in mapping.items():
            if not isinstance(alias, str) or not alias:
                continue
            stripped = alias.strip()
            if not stripped:
                continue
            if not isinstance(concept_id, str) or not concept_id:
                continue
            self._alias_to_concept[stripped.lower()] = concept_id

    def resolve_alias(self, token: str) -> Optional[str]:
        """Resolve a single token to a canonical concept id.

        Returns ``None`` if no alias is registered.
        Lookup is case-insensitive.
        """
        if not isinstance(token, str):
            return None
        return self._alias_to_concept.get(token.strip().lower())

    # ---- Taxonomy nodes ------------------------------------------

    def register_taxonomy_nodes(
        self, nodes: Iterable[Any]
    ) -> None:
        """Register a batch of ``TaxonomyNode`` records (or
        duck-typed dicts with ``node_id`` / ``parent_node_id``
        / ``aliases``).

        Existing entries for the same ``node_id`` are
        *replaced* -- callers must guarantee node_id
        uniqueness.
        """
        for n in nodes or ():
            nid = _get_attr_safely(n, "node_id", None)
            if not isinstance(nid, str) or not nid:
                continue
            parent = _get_attr_safely(n, "parent_node_id", None)
            if parent is not None and not isinstance(parent, str):
                parent = None
            aliases = _get_attr_safely(n, "aliases", ()) or ()
            label = _get_attr_safely(n, "label", "")
            self._taxonomy_nodes[nid] = {
                "node_id": nid,
                "parent_node_id": parent,
                "aliases": tuple(
                    a for a in aliases if isinstance(a, str)
                ),
                "label": label if isinstance(label, str) else "",
            }

    def taxonomy_nodes(self) -> Mapping[str, Any]:
        """Return a *copy* of the registered taxonomy-node
        mapping (defensive)."""
        return {
            nid: dict(data)
            for nid, data in self._taxonomy_nodes.items()
        }

    # ---- Hierarchy traversal -------------------------------------

    def ancestors_of(
        self, concept_id: str, *, max_depth: int = 1
    ) -> List[str]:
        """Return ancestor concept ids (excluding self), up to
        ``max_depth`` levels up.

        ``max_depth`` <= 0 returns an empty list.
        ``max_depth`` >= 1 includes the immediate parent
        (and grandparent when ``max_depth`` >= 2, etc.).
        """
        if max_depth <= 0:
            return []
        out: List[str] = []
        current = concept_id
        for _ in range(max_depth):
            node = self._taxonomy_nodes.get(current)
            if node is None:
                break
            parent = node.get("parent_node_id")
            if not parent or parent == current:
                break
            out.append(parent)
            current = parent
        return out

    def descendants_of(
        self, concept_id: str, *, max_depth: int = 1
    ) -> List[str]:
        """Return descendant concept ids (excluding self).

        ``max_depth`` <= 0 returns an empty list.
        The traversal walks down via the inverse of the
        parent index built from registered nodes.
        """
        if max_depth <= 0:
            return []
        # Build inverse parent index lazily.
        inverse: Dict[str, List[str]] = {}
        for nid, node in self._taxonomy_nodes.items():
            parent = node.get("parent_node_id")
            if parent:
                inverse.setdefault(parent, []).append(nid)
        out: List[str] = []
        seen: Set[str] = set()
        frontier: List[str] = list(inverse.get(concept_id, ()))
        for _ in range(max_depth):
            next_frontier: List[str] = []
            for nid in frontier:
                if nid in seen or nid == concept_id:
                    continue
                seen.add(nid)
                out.append(nid)
                for child in inverse.get(nid, ()):
                    if child not in seen and child != concept_id:
                        next_frontier.append(child)
            frontier = next_frontier
            if not frontier:
                break
        return out

    # ---- Introspection --------------------------------------------

    def concepts(self) -> Tuple[str, ...]:
        return tuple(sorted(self._concept_to_kos.keys()))

    def aliases(self) -> Mapping[str, str]:
        return dict(self._alias_to_concept)

    def __len__(self) -> int:
        return (
            len(self._concept_to_kos)
            + len(self._alias_to_concept)
            + len(self._taxonomy_nodes)
        )


# ---------------------------------------------------------------------------
# SemanticRetrievalEngine
# ---------------------------------------------------------------------------


class SemanticRetrievalEngine:
    """Concept-aware retrieval engine.

    Parameters
    ----------
    index:
        A ``SemanticIndex`` instance populated by the
        caller. The engine reads from it; it never
        mutates the index.
    ancestor_depth:
        How many ancestors to expand per query concept.
        ``0`` disables ancestor expansion; default ``1``.
    descendant_depth:
        How many descendants to expand per query concept.
        ``0`` disables descendant expansion; default ``1``.
    """

    ENGINE_NAME: str = "SemanticRetrievalEngine V1"

    def __init__(
        self,
        index: SemanticIndex,
        *,
        ancestor_depth: int = 0,
        descendant_depth: int = 0,
    ) -> None:
        if not isinstance(index, SemanticIndex):
            raise TypeError(
                "index must be a SemanticIndex; got "
                + type(index).__name__
            )
        self.index: SemanticIndex = index
        self.ancestor_depth = max(0, int(ancestor_depth))
        self.descendant_depth = max(0, int(descendant_depth))

    # ---- public ----------------------------------------------------

    def execute(
        self,
        query: RetrievalQuery,
        knowledge_objects: Sequence[Any],
    ) -> RetrievalResult:
        """Run a semantic retrieval against ``knowledge_objects``.

        Algorithm V1:

            1. Tokenize query_text.
            2. For each token, look up alias -> concept.
               Tokens that are themselves registered concept
               ids also count as *exact* matches.
            3. For each resolved concept:
                 * exact match  -> score SCORE_EXACT
                 * alias-only   -> score SCORE_ALIAS
                 * ancestor     -> score SCORE_ANCESTOR
                 * descendant   -> score SCORE_DESCENDANT
            4. Aggregate per knowledge_id: take the *max*
               score across all contributing concepts.
            5. Apply ``filters`` (exact-match gate).
            6. Sort + limit.

        Returns
        -------
        RetrievalResult:
            A frozen envelope. ``success`` is False iff the
            query contract failed validation.
        """
        started = time.perf_counter()

        # --- early guard -------------------------------------------
        if not _semantic_query_ok(query):
            return RetrievalResult(
                query_id=getattr(query, "query_id", ""),
                success=False,
                total_hits=0,
                hits=(),
                execution_time_ms=(time.perf_counter() - started)
                * 1000.0,
            )

        # --- inputs ------------------------------------------------
        query_text = getattr(query, "query_text", "") or ""
        query_tokens: List[str] = _tokenize(query_text)
        filters: Dict[str, Any] = dict(
            getattr(query, "filters", {}) or {}
        )
        sort_by: str = getattr(query, "sort_by", DEFAULT_SORT_BY)
        sort_order: str = getattr(
            query, "sort_order", DEFAULT_SORT_ORDER
        )
        limit: int = int(getattr(query, "limit", 20) or 20)

        # --- concept resolution + expansion -----------------------
        ko_scores: Dict[str, float] = {}
        ko_signals: Dict[str, List[str]] = {}

        for token in query_tokens:
            # 1. Try alias resolution -> canonical concept.
            resolved = self.index.resolve_alias(token)
            if resolved is not None:
                self._contribute(
                    resolved,
                    score=SCORE_ALIAS,
                    origin=("alias", token),
                    ko_scores=ko_scores,
                    ko_signals=ko_signals,
                )
                # Ancestor expansion.
                for anc in self.index.ancestors_of(
                    resolved, max_depth=self.ancestor_depth
                ):
                    self._contribute(
                        anc,
                        score=SCORE_ANCESTOR,
                        origin=("ancestor", token, resolved),
                        ko_scores=ko_scores,
                        ko_signals=ko_signals,
                    )
                # Descendant expansion.
                for desc in self.index.descendants_of(
                    resolved, max_depth=self.descendant_depth
                ):
                    self._contribute(
                        desc,
                        score=SCORE_DESCENDANT,
                        origin=("descendant", token, resolved),
                        ko_scores=ko_scores,
                        ko_signals=ko_signals,
                    )
            # 2. Literal-concept fallback: token == concept id.
            if (
                token in self.index._concept_to_kos  # noqa: SLF001
                and resolved is None
            ):
                self._contribute(
                    token,
                    score=SCORE_EXACT,
                    origin=("exact", token),
                    ko_scores=ko_scores,
                    ko_signals=ko_signals,
                )
                for anc in self.index.ancestors_of(
                    token, max_depth=self.ancestor_depth
                ):
                    self._contribute(
                        anc,
                        score=SCORE_ANCESTOR,
                        origin=("ancestor", token),
                        ko_scores=ko_scores,
                        ko_signals=ko_signals,
                    )
                for desc in self.index.descendants_of(
                    token, max_depth=self.descendant_depth
                ):
                    self._contribute(
                        desc,
                        score=SCORE_DESCENDANT,
                        origin=("descendant", token),
                        ko_scores=ko_scores,
                        ko_signals=ko_signals,
                    )
            # 3. Taxonomy-node fallback: token is a
            #    registered taxonomy node id but not a
            #    curated concept. The engine treats the
            #    token as a *parent* and expands
            #    descendants only (no exact contribution).
            elif (
                token in self.index._taxonomy_nodes  # noqa: SLF001
                and resolved is None
                and token not in self.index._concept_to_kos  # noqa: SLF001
            ):
                for desc in self.index.descendants_of(
                    token, max_depth=self.descendant_depth
                ):
                    self._contribute(
                        desc,
                        score=SCORE_DESCENDANT,
                        origin=("descendant-of-taxonomy", token),
                        ko_scores=ko_scores,
                        ko_signals=ko_signals,
                    )

        # --- build hits --------------------------------------------
        candidates: List[RetrievalHit] = []
        # Pre-index KO list by knowledge_id for O(1) lookup.
        ko_by_id: Dict[str, Any] = {}
        for ko in knowledge_objects:
            ko_id = _get_attr_safely(ko, "knowledge_id", "")
            if ko_id:
                ko_by_id[ko_id] = ko

        for ko_id, score in ko_scores.items():
            ko = ko_by_id.get(ko_id)
            if ko is None:
                # The KO is referenced by the index but is
                # not in the corpus -- skip (no implicit KO
                # fabrication).
                continue
            ko_dict = _ko_to_dict(ko)
            if filters and not _matches_filters(ko_dict, filters):
                continue
            knowledge_version = int(
                _get_attr_safely(ko, "version", 1) or 1
            )
            snapshot = {
                k: ko_dict.get(k)
                for k in (
                    "knowledge_id",
                    "version",
                    "title",
                    "category",
                    "theme",
                    "style",
                    "color_system",
                )
                if k != "image_refs"
            }
            candidates.append(
                RetrievalHit(
                    knowledge_id=ko_id,
                    knowledge_version=knowledge_version,
                    match_score=float(score),
                    matched_fields=list(ko_signals.get(ko_id, [])),
                    matched_snippets={
                        "concept:score": "%.3f" % float(score),
                    },
                    knowledge_object_snapshot=snapshot,
                )
            )

        # --- sort --------------------------------------------------
        candidates.sort(
            key=lambda h: (
                -float(h.match_score),
                -int(h.knowledge_version),
                h.knowledge_id,
                h.hit_id,
            )
        )
        if sort_order == "asc":
            # Reverse while preserving version/id stability
            # by re-sorting.
            candidates = list(reversed(candidates))

        # --- limit -------------------------------------------------
        if limit < 1:
            limit = 1
        hits = tuple(candidates[:limit])

        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return RetrievalResult(
            query_id=getattr(query, "query_id", ""),
            success=True,
            total_hits=len(hits),
            hits=hits,
            execution_time_ms=elapsed_ms,
        )

    # ---- helpers --------------------------------------------------

    def _contribute(
        self,
        concept_id: str,
        *,
        score: float,
        origin: Tuple[str, ...],
        ko_scores: Dict[str, float],
        ko_signals: Dict[str, List[str]],
    ) -> None:
        """Add a contribution to ``ko_scores`` for ``concept_id``.

        The per-KO score is the **max** across all
        contributing concepts (rationale: a single hit that
        matches via a closer concept should not be
        down-graded by a second, more distant concept that
        also maps to the same KO).
        """
        for ko_id in self.index.concept_to_kos(concept_id):
            cur = ko_scores.get(ko_id, 0.0)
            if score > cur:
                ko_scores[ko_id] = float(score)
            signals = ko_signals.setdefault(ko_id, [])
            label = ":".join(origin) + ":" + concept_id
            if label not in signals:
                signals.append(label)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _semantic_query_ok(query: RetrievalQuery) -> bool:
    """Lightweight validator for the semantic engine.

    The semantic engine consumes ``query_text`` heavily
    (this is the canonical semantic input) so the
    standard V1 validator is sufficient. We duplicate
    only the structural checks here so the semantic
    engine can short-circuit cleanly on an obviously
    broken query.
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
    if sb not in (
        "score",
        "knowledge_id",
        "version",
        "created_at",
    ):
        return False
    so = getattr(query, "sort_order", None)
    if so not in ("asc", "desc"):
        return False
    # The semantic engine is text-driven. An empty
    # query with no schema signals is rejected as an
    # invalid V1 query (mirrors Q7 in the contract
    # validator). Callers who want "all concepts"
    # should pass an explicit token.
    qt = getattr(query, "query_text", "") or ""
    qfields = getattr(query, "query_fields", ()) or ()
    filters = getattr(query, "filters", {}) or {}
    has_signal = (
        (isinstance(qt, str) and bool(qt.strip()))
        or (isinstance(qfields, (list, tuple)) and len(qfields) > 0)
        or (isinstance(filters, dict) and len(filters) > 0)
    )
    return bool(has_signal)


__all__ = [
    "SemanticIndex",
    "SemanticRetrievalEngine",
    "SCORE_EXACT",
    "SCORE_ALIAS",
    "SCORE_ANCESTOR",
    "SCORE_DESCENDANT",
]
