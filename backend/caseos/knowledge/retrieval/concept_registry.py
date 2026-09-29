"""Semantic Concept Registry V1 (Sprint 24.1-B).

This module ships the **append-only registry layer** for
semantic concepts and their aliases. It complements the
``SemanticIndex`` (Sprint 24.1-A) which holds the *runtime*
in-memory view consumed by ``SemanticRetrievalEngine``.

Architectural role:

    Sprint 24.1-A
        SemanticIndex              -- runtime in-memory view
                                       (caller-side)
        SemanticRetrievalEngine    -- consumer
    Sprint 24.1-B (THIS MODULE)
        ConceptRecord              -- canonical record shape
        ConceptRegistry            -- append-only container
        ConceptAliasRecord         -- alias record shape
        ConceptAliasRegistry       -- append-only alias container
        build_semantic_index       -- registry -> SemanticIndex
                                       bridge

Both registries follow the same append-only contract as
``AttributeRegistry`` (Sprint 23.1-D):

    Allowed methods:
        * append(record)
        * get(record_id)
        * list()
        * count()
        * for_concept_type(concept_type)
        * roots() / children_of(concept_id)
        * ancestors_of(concept_id, max_depth)
        * descendants_of(concept_id, max_depth)

    Forbidden methods (raise TypeError):
        * update
        * delete
        * overwrite
        * clear

Architecture boundary (Sprint 24.1-B spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
        * caseos.brain.*
    This module MAY import from:
        * caseos.knowledge.object          (KO schema)
        * caseos.knowledge.attribute       (sibling registry)
        * caseos.knowledge.domain          (sibling registry)
        * caseos.knowledge.binding         (sibling registry)
        * caseos.knowledge.taxonomy        (sibling registry)
        * caseos.knowledge.graph           (sibling graph)
        * caseos.knowledge.retrieval       (sibling SemanticIndex)
        * stdlib
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)


# ---------------------------------------------------------------------------
# Defaults and constants
# ---------------------------------------------------------------------------


#: Concept type allow-list. Adding a new concept type
#: requires extending this set AND a schema-review Sprint
#: to confirm downstream consumers understand it.
CONCEPT_TYPE_ALLOW_LIST: frozenset = frozenset(
    {
        "theme",
        "style",
        "function",
        "category",
        "domain_marker",
    }
)

#: Default locale for alias records.
DEFAULT_LOCALE: str = "en"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _empty_tuple_str() -> tuple:
    return ()


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ConceptRegistryError(ValueError):
    """Base error for the concept registry layer."""


class ConceptRecordError(ConceptRegistryError):
    """Raised by ``ConceptRecord.__post_init__`` on a
    structural violation (missing field, wrong type,
    unknown concept_type, etc.).
    """


class AliasRegistryError(ConceptRegistryError):
    """Base error for the alias registry layer."""


class ConceptAliasRecordError(AliasRegistryError):
    """Raised by ``ConceptAliasRecord.__post_init__`` on a
    structural violation.
    """


# ---------------------------------------------------------------------------
# ConceptRecord
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConceptRecord:
    """A canonical concept in the CaseOS semantic layer.

    Fields are grouped as:

        Identity
            concept_id, version
        Content
            label, description, concept_type
        Hierarchy
            parent_concept_id
        Bindings
            knowledge_object_ids
        Aliases
            aliases
        Metadata
            created_at, updated_at, created_by, source

    The dataclass is frozen; collection fields
    (``aliases``, ``knowledge_object_ids``) are deep-copied
    in ``__post_init__`` so caller mutations cannot leak
    into the record.
    """

    # ---- Identity --------------------------------------------------
    concept_id: str
    version: int = 1

    # ---- Content ---------------------------------------------------
    label: str = ""
    description: str = ""
    concept_type: str = "theme"

    # ---- Hierarchy -------------------------------------------------
    parent_concept_id: Optional[str] = None

    # ---- Bindings --------------------------------------------------
    knowledge_object_ids: tuple = field(
        default_factory=_empty_tuple_str,
    )

    # ---- Aliases ---------------------------------------------------
    aliases: tuple = field(default_factory=_empty_tuple_str)

    # ---- Metadata --------------------------------------------------
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    created_by: str = ""
    source: str = ""

    def __post_init__(self) -> None:
        # Defensive deep-copy of collection fields.
        for fname in ("knowledge_object_ids", "aliases"):
            raw = getattr(self, fname)
            if isinstance(raw, (list, tuple)):
                object.__setattr__(
                    self, fname, tuple(copy.deepcopy(list(raw))),
                )
            elif raw is None:
                object.__setattr__(self, fname, ())
            else:
                raise ConceptRecordError(
                    fname + " must be a list/tuple; got "
                    + type(raw).__name__
                )

        # Identity + version guards.
        if (
            not isinstance(self.concept_id, str)
            or not self.concept_id.strip()
        ):
            raise ConceptRecordError(
                "concept_id must be a non-empty string"
            )
        if (
            not isinstance(self.version, int)
            or isinstance(self.version, bool)
            or self.version < 1
        ):
            raise ConceptRecordError(
                "version must be a positive integer (>= 1); got "
                + repr(self.version)
            )
        # Concept-type guard.
        if (
            not isinstance(self.concept_type, str)
            or self.concept_type not in CONCEPT_TYPE_ALLOW_LIST
        ):
            raise ConceptRecordError(
                "concept_type must be one of "
                + ", ".join(sorted(CONCEPT_TYPE_ALLOW_LIST))
                + "; got "
                + repr(self.concept_type)
            )
        # Parent ID guard (None or non-empty string).
        if (
            self.parent_concept_id is not None
            and (
                not isinstance(self.parent_concept_id, str)
                or not self.parent_concept_id.strip()
            )
        ):
            raise ConceptRecordError(
                "parent_concept_id must be None or a non-empty string"
            )

    # ---- Serialization --------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "version": self.version,
            "label": self.label,
            "description": self.description,
            "concept_type": self.concept_type,
            "parent_concept_id": self.parent_concept_id,
            "knowledge_object_ids": list(self.knowledge_object_ids),
            "aliases": list(self.aliases),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "source": self.source,
        }

    @staticmethod
    def from_dict(data: Mapping[str, Any]) -> "ConceptRecord":
        if not isinstance(data, Mapping):
            raise ConceptRecordError(
                "from_dict expects a mapping; got " + type(data).__name__
            )
        kwargs: dict[str, Any] = {}
        for fname in (
            "concept_id",
            "version",
            "label",
            "description",
            "concept_type",
            "parent_concept_id",
            "created_at",
            "updated_at",
            "created_by",
            "source",
        ):
            if fname in data:
                kwargs[fname] = data[fname]
        for fname in ("knowledge_object_ids", "aliases"):
            if fname in data:
                raw = data[fname]
                if raw is None:
                    kwargs[fname] = ()
                elif isinstance(raw, (list, tuple)):
                    kwargs[fname] = tuple(raw)
                else:
                    raise ConceptRecordError(
                        fname + " must be a list/tuple; got "
                        + type(raw).__name__
                    )
        return ConceptRecord(**kwargs)


# ---------------------------------------------------------------------------
# ConceptRegistry
# ---------------------------------------------------------------------------


class ConceptRegistry:
    """Append-only container for ``ConceptRecord`` records.

    Mirrors the ``AttributeRegistry`` (Sprint 23.1-D) contract:
    callers can ``append`` and read; update / delete /
    overwrite / clear are forbidden and raise ``TypeError``.

    The registry is intentionally small. Future Sprints may
    add cross-record validation (e.g. cycle detection on
    ``parent_concept_id``) as a separate validator class --
    it does NOT live here.
    """

    def __init__(self) -> None:
        self._records: List[ConceptRecord] = []

    # ---- Allowed operations ----------------------------------------

    def append(self, record: ConceptRecord) -> ConceptRecord:
        """Append a record. Returns the appended record.

        The registry does NOT enforce uniqueness of
        ``concept_id`` -- callers (or a future validator
        pass) are responsible for that.
        """
        if not isinstance(record, ConceptRecord):
            raise ConceptRegistryError(
                "record must be a ConceptRecord instance; got "
                + type(record).__name__
            )
        self._records.append(record)
        return record

    def get(self, concept_id: str) -> Optional[ConceptRecord]:
        """Return the *first* record whose ``concept_id``
        matches. ``None`` when no such record exists."""
        if not isinstance(concept_id, str):
            return None
        for r in self._records:
            if r.concept_id == concept_id:
                return r
        return None

    def list(self) -> List[ConceptRecord]:
        """Return a shallow copy of the stored records."""
        return list(self._records)

    def count(self) -> int:
        return len(self._records)

    def concept_ids(self) -> List[str]:
        """Return the registered concept ids in registration order."""
        seen: List[str] = []
        for r in self._records:
            if r.concept_id not in seen:
                seen.append(r.concept_id)
        return seen

    def for_concept_type(
        self, concept_type: str
    ) -> List[ConceptRecord]:
        return [r for r in self._records if r.concept_type == concept_type]

    def roots(self) -> List[ConceptRecord]:
        """Records with no parent (top of the hierarchy)."""
        return [r for r in self._records if r.parent_concept_id is None]

    def children_of(self, concept_id: str) -> List[ConceptRecord]:
        return [
            r for r in self._records if r.parent_concept_id == concept_id
        ]

    # ---- Hierarchy traversal --------------------------------------

    def ancestors_of(
        self, concept_id: str, *, max_depth: int = 1
    ) -> List[ConceptRecord]:
        """Return ancestor records (excluding self), up to
        ``max_depth`` levels up."""
        if max_depth <= 0:
            return []
        out: List[ConceptRecord] = []
        current = self.get(concept_id)
        for _ in range(max_depth):
            if current is None or current.parent_concept_id is None:
                break
            parent = self.get(current.parent_concept_id)
            if parent is None:
                break
            out.append(parent)
            current = parent
        return out

    def descendants_of(
        self, concept_id: str, *, max_depth: int = 1
    ) -> List[ConceptRecord]:
        """Return descendant records (excluding self)."""
        if max_depth <= 0:
            return []
        out: List[ConceptRecord] = []
        seen: set = set()
        frontier = list(self.children_of(concept_id))
        for _ in range(max_depth):
            next_frontier: List[ConceptRecord] = []
            for child in frontier:
                if child.concept_id in seen or child.concept_id == concept_id:
                    continue
                seen.add(child.concept_id)
                out.append(child)
                for grand in self.children_of(child.concept_id):
                    if (
                        grand.concept_id not in seen
                        and grand.concept_id != concept_id
                    ):
                        next_frontier.append(grand)
            frontier = next_frontier
            if not frontier:
                break
        return out

    # ---- Forbidden operations --------------------------------------

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "ConceptRegistry.update is forbidden; registry is append-only"
        )

    def delete(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "ConceptRegistry.delete is forbidden; registry is append-only"
        )

    def overwrite(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "ConceptRegistry.overwrite is forbidden; registry is append-only"
        )

    def clear(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "ConceptRegistry.clear is forbidden; registry is append-only"
        )


# ---------------------------------------------------------------------------
# ConceptAliasRecord
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConceptAliasRecord:
    """A canonical alias -> concept mapping.

    Aliases are *lowercase* on entry. Each alias belongs to
    a single locale (``locale`` defaults to ``"en"``).
    """

    alias_id: str
    version: int = 1
    alias: str = ""
    canonical_concept_id: str = ""
    locale: str = DEFAULT_LOCALE
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    created_by: str = ""
    source: str = ""

    def __post_init__(self) -> None:
        if (
            not isinstance(self.alias_id, str)
            or not self.alias_id.strip()
        ):
            raise ConceptAliasRecordError(
                "alias_id must be a non-empty string"
            )
        if (
            not isinstance(self.version, int)
            or isinstance(self.version, bool)
            or self.version < 1
        ):
            raise ConceptAliasRecordError(
                "version must be a positive integer (>= 1); got "
                + repr(self.version)
            )
        if (
            not isinstance(self.alias, str)
            or not self.alias.strip()
        ):
            raise ConceptAliasRecordError(
                "alias must be a non-empty string"
            )
        if (
            not isinstance(self.canonical_concept_id, str)
            or not self.canonical_concept_id.strip()
        ):
            raise ConceptAliasRecordError(
                "canonical_concept_id must be a non-empty string"
            )
        # Lowercase the alias on entry -- the registry is
        # case-insensitive.
        object.__setattr__(self, "alias", self.alias.strip().lower())

    def to_dict(self) -> dict[str, Any]:
        return {
            "alias_id": self.alias_id,
            "version": self.version,
            "alias": self.alias,
            "canonical_concept_id": self.canonical_concept_id,
            "locale": self.locale,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "source": self.source,
        }

    @staticmethod
    def from_dict(data: Mapping[str, Any]) -> "ConceptAliasRecord":
        if not isinstance(data, Mapping):
            raise ConceptAliasRecordError(
                "from_dict expects a mapping; got " + type(data).__name__
            )
        kwargs: dict[str, Any] = {}
        for fname in (
            "alias_id",
            "version",
            "alias",
            "canonical_concept_id",
            "locale",
            "created_at",
            "updated_at",
            "created_by",
            "source",
        ):
            if fname in data:
                kwargs[fname] = data[fname]
        return ConceptAliasRecord(**kwargs)


# ---------------------------------------------------------------------------
# ConceptAliasRegistry
# ---------------------------------------------------------------------------


class ConceptAliasRegistry:
    """Append-only container for ``ConceptAliasRecord`` records.

    Lookups are case-insensitive (the record's
    ``__post_init__`` already lowercases the alias on entry).
    """

    def __init__(self) -> None:
        self._records: List[ConceptAliasRecord] = []

    # ---- Allowed operations ----------------------------------------

    def append(self, record: ConceptAliasRecord) -> ConceptAliasRecord:
        if not isinstance(record, ConceptAliasRecord):
            raise AliasRegistryError(
                "record must be a ConceptAliasRecord; got "
                + type(record).__name__
            )
        self._records.append(record)
        return record

    def get(self, alias_id: str) -> Optional[ConceptAliasRecord]:
        if not isinstance(alias_id, str):
            return None
        for r in self._records:
            if r.alias_id == alias_id:
                return r
        return None

    def resolve(self, alias: str) -> Optional[str]:
        """Resolve an alias to its canonical concept id.

        Returns ``None`` when the alias is not registered.
        Lookup is case-insensitive (the record stores
        lowercase aliases).
        """
        if not isinstance(alias, str):
            return None
        needle = alias.strip().lower()
        if not needle:
            return None
        for r in self._records:
            if r.alias == needle:
                return r.canonical_concept_id
        return None

    def for_concept(self, concept_id: str) -> List[ConceptAliasRecord]:
        return [
            r for r in self._records
            if r.canonical_concept_id == concept_id
        ]

    def list(self) -> List[ConceptAliasRecord]:
        return list(self._records)

    def count(self) -> int:
        return len(self._records)

    def alias_ids(self) -> List[str]:
        seen: List[str] = []
        for r in self._records:
            if r.alias_id not in seen:
                seen.append(r.alias_id)
        return seen

    # ---- Forbidden operations --------------------------------------

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "ConceptAliasRegistry.update is forbidden; registry is append-only"
        )

    def delete(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "ConceptAliasRegistry.delete is forbidden; registry is append-only"
        )

    def overwrite(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "ConceptAliasRegistry.overwrite is forbidden; registry is append-only"
        )

    def clear(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "ConceptAliasRegistry.clear is forbidden; registry is append-only"
        )


# ---------------------------------------------------------------------------
# Bridge: registries -> SemanticIndex (Sprint 24.1-A)
# ---------------------------------------------------------------------------


def build_semantic_index(
    concept_registry: ConceptRegistry,
    alias_registry: ConceptAliasRegistry,
) -> Any:
    """Build a ``SemanticIndex`` from the two registries.

    The bridge translates the canonical record shapes into
    the simpler in-memory tables expected by
    ``SemanticRetrievalEngine``. It is intentionally a one-
    way data pump -- registries remain append-only and the
    index is treated as a derived view.

    Returns
    -------
    SemanticIndex
        A fresh ``SemanticIndex`` populated with the
        registry's current contents. The index is the
        only consumer-facing artefact for the
        ``SemanticRetrievalEngine``.

    Raises
    ------
    ConceptRegistryError
        If ``concept_registry`` is not a
        ``ConceptRegistry``.
    AliasRegistryError
        If ``alias_registry`` is not a
        ``ConceptAliasRegistry``.
    """
    # Local import: avoid a hard dependency at module-load
    # time so the registry layer stays usable on its own.
    from .semantic import SemanticIndex

    if not isinstance(concept_registry, ConceptRegistry):
        raise ConceptRegistryError(
            "concept_registry must be a ConceptRegistry; got "
            + type(concept_registry).__name__
        )
    if not isinstance(alias_registry, ConceptAliasRegistry):
        raise AliasRegistryError(
            "alias_registry must be a ConceptAliasRegistry; got "
            + type(alias_registry).__name__
        )

    index = SemanticIndex()

    # 1. Concept -> KO membership.
    concept_to_kos: Dict[str, List[str]] = {}
    for record in concept_registry.list():
        bucket = concept_to_kos.setdefault(record.concept_id, [])
        for ko_id in record.knowledge_object_ids:
            if isinstance(ko_id, str) and ko_id and ko_id not in bucket:
                bucket.append(ko_id)
    index.register_concept_to_kos(concept_to_kos)

    # 2. Aliases registered on each concept (denormalized
    #    ``ConceptRecord.aliases``) PLUS standalone
    #    ``ConceptAliasRecord`` entries.
    alias_to_concept: Dict[str, str] = {}
    for record in concept_registry.list():
        for alias in record.aliases:
            if isinstance(alias, str) and alias:
                alias_to_concept.setdefault(
                    alias.strip().lower(), record.concept_id,
                )
    for arec in alias_registry.list():
        alias_to_concept[arec.alias] = arec.canonical_concept_id
    index.register_aliases(alias_to_concept)

    # 3. Taxonomy-node view: every concept becomes a node.
    node_payloads = []
    for record in concept_registry.list():
        node_payloads.append({
            "node_id": record.concept_id,
            "parent_node_id": record.parent_concept_id,
            "aliases": list(record.aliases),
            "label": record.label,
        })
    index.register_taxonomy_nodes(node_payloads)

    return index


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


__all__ = [
    "ConceptRecord",
    "ConceptRegistry",
    "ConceptAliasRecord",
    "ConceptAliasRegistry",
    "ConceptRegistryError",
    "AliasRegistryError",
    "ConceptRecordError",
    "ConceptAliasRecordError",
    "CONCEPT_TYPE_ALLOW_LIST",
    "DEFAULT_LOCALE",
    "build_semantic_index",
]
