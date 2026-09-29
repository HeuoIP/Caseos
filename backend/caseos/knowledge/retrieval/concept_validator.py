"""Semantic Concept Registry Validator V1 (Sprint 24.2-A).

This module ships the **runtime guard** that enforces
schema + cross-record invariants on the records produced
by Sprint 24.1-B's ``ConceptRegistry`` and
``ConceptAliasRegistry``. The validators are stateless
and follow the same pattern as ``TaxonomyValidator``
(Sprint 23.1-C) and ``KnowledgeAttributeValidator``
(Sprint 23.1-D).

Single-record checks (ConceptRecord) -- C1..C7:

    C1  concept_id is a non-empty string
    C2  version is a positive integer (>= 1) and not a bool
    C3  concept_type is in CONCEPT_TYPE_ALLOW_LIST
    C4  parent_concept_id, when not None, is a non-empty
        string (and not equal to concept_id -- no self-ref)
    C5  every knowledge_object_ids entry is a non-empty
        string
    C6  every aliases entry is a non-empty string
    C7  created_at and updated_at are strings (empty
        string is allowed -- the dataclass defaults to
        a generated ISO timestamp on construction)

Cross-record checks (ConceptRecord, requires registry) --
C8:

    C8.1 concept_id is unique within the registry
    C8.2 parent_concept_id, when present, must refer to a
         concept_id that exists in the registry
    C8.3 the parent chain does not contain a cycle

Single-record checks (ConceptAliasRecord) -- A1..A4:

    A1  alias_id is a non-empty string
    A2  version is a positive integer (>= 1) and not a bool
    A3  alias is a non-empty string after stripping /
        lowercasing (the record's __post_init__ already
        lowercases; the validator confirms the post-state)
    A4  canonical_concept_id is a non-empty string

Cross-record checks (ConceptAliasRecord) -- A5:

    A5.1 alias_id is unique within the alias registry
    A5.2 canonical_concept_id, when concept_registry is
         supplied, must refer to a concept_id that exists
    A5.3 the alias string is unique across the alias
         registry (case-insensitive)

Architecture boundary (Sprint 24.2-A spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
        * caseos.brain.*
    This module MAY import from:
        * caseos.knowledge.retrieval  (sibling modules)
        * stdlib
"""
from __future__ import annotations

import dataclasses
from typing import Any, Iterable, Optional, Tuple

from .concept_registry import (
    CONCEPT_TYPE_ALLOW_LIST,
    ConceptAliasRecord,
    ConceptRecord,
)


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class ConceptValidationResult:
    """Outcome of ``ConceptValidator.validate``.

    Fields
    ------
    valid:
        True iff every rule passed.
    errors:
        Tuple of human-readable error messages. Empty
        when ``valid`` is True.
    rule_failures:
        Tuple of rule identifiers that failed (C1..C8).
        Useful for diagnostic output.
    """

    valid: bool
    errors: Tuple[str, ...] = ()
    rule_failures: Tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class ConceptAliasValidationResult:
    """Outcome of ``ConceptAliasValidator.validate``."""

    valid: bool
    errors: Tuple[str, ...] = ()
    rule_failures: Tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_positive_int(value: Any) -> bool:
    # Reject bool explicitly (bool is a subclass of int).
    if isinstance(value, bool):
        return False
    return isinstance(value, int) and value >= 1


# ---------------------------------------------------------------------------
# ConceptValidator
# ---------------------------------------------------------------------------


class ConceptValidator:
    """Stateless validator for ``ConceptRecord``.

    Single-record rules (C1..C7) always run. Cross-record
    rules (C8) activate when ``concept_registry`` is supplied.
    The registry argument is duck-typed: any object with a
    ``concept_ids()`` method and a ``get(concept_id)``
    accessor is accepted (the canonical input is a
    ``ConceptRegistry`` from Sprint 24.1-B).
    """

    def validate(
        self,
        record: Optional[ConceptRecord],
        *,
        concept_registry: Optional[Any] = None,
    ) -> ConceptValidationResult:
        errors: list[str] = []
        failed: list[str] = []

        if record is None:
            return ConceptValidationResult(
                valid=False,
                errors=("record is None",),
                rule_failures=("C0",),
            )

        # ---- C1: concept_id -------------------------------------
        cid = getattr(record, "concept_id", None)
        if not _is_nonempty_str(cid):
            errors.append("C1: concept_id must be a non-empty string")
            failed.append("C1")

        # ---- C2: version -----------------------------------------
        version = getattr(record, "version", None)
        if not _is_positive_int(version):
            errors.append(
                "C2: version must be a positive integer (>= 1); got "
                + repr(version)
            )
            failed.append("C2")

        # ---- C3: concept_type -----------------------------------
        ct = getattr(record, "concept_type", None)
        if (
            not isinstance(ct, str)
            or ct not in CONCEPT_TYPE_ALLOW_LIST
        ):
            errors.append(
                "C3: concept_type must be one of "
                + ", ".join(sorted(CONCEPT_TYPE_ALLOW_LIST))
                + "; got "
                + repr(ct)
            )
            failed.append("C3")

        # ---- C4: parent_concept_id ------------------------------
        parent = getattr(record, "parent_concept_id", None)
        if parent is not None:
            if not _is_nonempty_str(parent):
                errors.append(
                    "C4: parent_concept_id, when not None, must be "
                    "a non-empty string"
                )
                failed.append("C4")
            elif isinstance(cid, str) and parent == cid:
                errors.append(
                    "C4: parent_concept_id must not equal concept_id "
                    "(no self-reference)"
                )
                failed.append("C4")

        # ---- C5: knowledge_object_ids ---------------------------
        kos = getattr(record, "knowledge_object_ids", ()) or ()
        if not isinstance(kos, (list, tuple)):
            errors.append(
                "C5: knowledge_object_ids must be a list/tuple"
            )
            failed.append("C5")
        else:
            for kid in kos:
                if not _is_nonempty_str(kid):
                    errors.append(
                        "C5: every knowledge_object_ids entry must be "
                        "a non-empty string; got " + repr(kid)
                    )
                    failed.append("C5")
                    break

        # ---- C6: aliases ----------------------------------------
        aliases = getattr(record, "aliases", ()) or ()
        if not isinstance(aliases, (list, tuple)):
            errors.append("C6: aliases must be a list/tuple")
            failed.append("C6")
        else:
            for alias in aliases:
                if not _is_nonempty_str(alias):
                    errors.append(
                        "C6: every aliases entry must be a non-empty "
                        "string; got " + repr(alias)
                    )
                    failed.append("C6")
                    break

        # ---- C7: created_at / updated_at ------------------------
        for fname in ("created_at", "updated_at"):
            v = getattr(record, fname, None)
            if v is not None and not isinstance(v, str):
                errors.append(
                    "C7: " + fname + " must be a string; got "
                    + type(v).__name__
                )
                failed.append("C7")

        # ---- C8: cross-record -----------------------------------
        if concept_registry is not None:
            cross_errs, cross_failed = self._check_cross_record(
                record, concept_registry
            )
            errors.extend(cross_errs)
            failed.extend(cross_failed)

        return ConceptValidationResult(
            valid=(len(errors) == 0),
            errors=tuple(errors),
            rule_failures=tuple(failed),
        )

    # ---- private --------------------------------------------------

    def _check_cross_record(
        self,
        record: ConceptRecord,
        registry: Any,
    ) -> Tuple[list[str], list[str]]:
        errors: list[str] = []
        failed: list[str] = []
        cid = getattr(record, "concept_id", None)

        # ---- C8.1: concept_id unique ----------------------------
        try:
            ids = list(registry.concept_ids())
        except AttributeError:
            # Duck-typed registry without concept_ids() --
            # treat as unknown shape and skip.
            return errors, failed
        if isinstance(cid, str):
            count = sum(1 for x in ids if x == cid)
            if count > 1:
                errors.append(
                    "C8.1: concept_id is not unique within the registry "
                    "(found " + str(count) + " entries with id "
                    + repr(cid) + ")"
                )
                failed.append("C8.1")

        # ---- C8.2: parent_concept_id must exist -----------------
        parent = getattr(record, "parent_concept_id", None)
        if isinstance(parent, str) and parent:
            try:
                parent_record = registry.get(parent)
            except Exception:
                parent_record = None
            if parent_record is None:
                errors.append(
                    "C8.2: parent_concept_id "
                    + repr(parent)
                    + " does not refer to an existing concept"
                )
                failed.append("C8.2")

        # ---- C8.3: no cycle -------------------------------------
        if isinstance(cid, str) and isinstance(parent, str) and parent:
            visited: set = set()
            current_parent: Optional[str] = parent
            try:
                # Walk up the chain. If we ever see cid
                # again, there's a cycle.
                while isinstance(current_parent, str) and current_parent:
                    if current_parent == cid:
                        errors.append(
                            "C8.3: parent chain for concept_id "
                            + repr(cid)
                            + " contains a cycle"
                        )
                        failed.append("C8.3")
                        break
                    if current_parent in visited:
                        # The chain is acyclic up to this
                        # point but visits an already-known
                        # non-cid node -> safe.
                        break
                    visited.add(current_parent)
                    try:
                        next_record = registry.get(current_parent)
                    except Exception:
                        next_record = None
                    if next_record is None:
                        break
                    current_parent = getattr(
                        next_record, "parent_concept_id", None
                    )
                    if current_parent is None:
                        break
            except Exception:
                # Cycle detection must never raise -- if it
                # does, treat the chain as untrusted and
                # reject the record.
                errors.append(
                    "C8.3: parent chain for concept_id "
                    + repr(cid) + " could not be safely walked"
                )
                failed.append("C8.3")

        return errors, failed


# ---------------------------------------------------------------------------
# ConceptAliasValidator
# ---------------------------------------------------------------------------


class ConceptAliasValidator:
    """Stateless validator for ``ConceptAliasRecord``.

    Single-record rules (A1..A4) always run. Cross-record
    rules (A5) activate when ``alias_registry`` is supplied
    (and optionally ``concept_registry`` for A5.2).
    """

    def validate(
        self,
        record: Optional[ConceptAliasRecord],
        *,
        alias_registry: Optional[Any] = None,
        concept_registry: Optional[Any] = None,
    ) -> ConceptAliasValidationResult:
        errors: list[str] = []
        failed: list[str] = []

        if record is None:
            return ConceptAliasValidationResult(
                valid=False,
                errors=("record is None",),
                rule_failures=("A0",),
            )

        # ---- A1: alias_id ---------------------------------------
        aid = getattr(record, "alias_id", None)
        if not _is_nonempty_str(aid):
            errors.append("A1: alias_id must be a non-empty string")
            failed.append("A1")

        # ---- A2: version ----------------------------------------
        version = getattr(record, "version", None)
        if not _is_positive_int(version):
            errors.append(
                "A2: version must be a positive integer (>= 1); got "
                + repr(version)
            )
            failed.append("A2")

        # ---- A3: alias ------------------------------------------
        alias = getattr(record, "alias", None)
        if not _is_nonempty_str(alias):
            errors.append("A3: alias must be a non-empty string")
            failed.append("A3")

        # ---- A4: canonical_concept_id ---------------------------
        canonical = getattr(record, "canonical_concept_id", None)
        if not _is_nonempty_str(canonical):
            errors.append(
                "A4: canonical_concept_id must be a non-empty string"
            )
            failed.append("A4")

        # ---- A5: cross-record -----------------------------------
        if alias_registry is not None:
            cross_errs, cross_failed = self._check_cross_record(
                record, alias_registry, concept_registry
            )
            errors.extend(cross_errs)
            failed.extend(cross_failed)

        return ConceptAliasValidationResult(
            valid=(len(errors) == 0),
            errors=tuple(errors),
            rule_failures=tuple(failed),
        )

    # ---- private --------------------------------------------------

    def _check_cross_record(
        self,
        record: ConceptAliasRecord,
        alias_registry: Any,
        concept_registry: Optional[Any],
    ) -> Tuple[list[str], list[str]]:
        errors: list[str] = []
        failed: list[str] = []
        aid = getattr(record, "alias_id", None)
        alias = getattr(record, "alias", None)
        canonical = getattr(record, "canonical_concept_id", None)

        # ---- A5.1: alias_id unique ------------------------------
        try:
            existing_ids = list(alias_registry.alias_ids())
        except AttributeError:
            return errors, failed
        if isinstance(aid, str):
            count = sum(1 for x in existing_ids if x == aid)
            if count > 1:
                errors.append(
                    "A5.1: alias_id is not unique within the alias "
                    "registry (found " + str(count) + " entries with id "
                    + repr(aid) + ")"
                )
                failed.append("A5.1")

        # ---- A5.2: canonical_concept_id refers to existing -----
        if (
            isinstance(canonical, str)
            and canonical
            and concept_registry is not None
        ):
            try:
                canonical_record = concept_registry.get(canonical)
            except Exception:
                canonical_record = None
            if canonical_record is None:
                errors.append(
                    "A5.2: canonical_concept_id "
                    + repr(canonical)
                    + " does not refer to an existing concept"
                )
                failed.append("A5.2")

        # ---- A5.3: alias string unique (case-insensitive) ------
        if isinstance(alias, str) and alias:
            try:
                existing = list(alias_registry.list())
            except AttributeError:
                existing = []
            needle = alias.strip().lower()
            collisions = [
                r for r in existing
                if getattr(r, "alias", None) == needle
                and getattr(r, "alias_id", None) != aid
            ]
            if collisions:
                errors.append(
                    "A5.3: alias string "
                    + repr(alias)
                    + " is not unique across the alias registry "
                    "(collides with "
                    + str(len(collisions))
                    + " other record(s))"
                )
                failed.append("A5.3")

        return errors, failed


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


__all__ = [
    "ConceptValidator",
    "ConceptAliasValidator",
    "ConceptValidationResult",
    "ConceptAliasValidationResult",
]
