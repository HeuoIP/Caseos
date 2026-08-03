"""Evolution Change Policy V1 (Sprint 22.4-B, ADR-020).

The policy describes **which Knowledge fields the evolution
layer is allowed to change** in V1. It is a pure data
declaration: no I/O, no side effects, no state.

Allowed change types V1 (Sprint 22.4-B spec Task 1):

    boundary_update
    principle_update
    applicability_update

These correspond to the three ADR-018 Section 3.A fields that
the Feedback Learning Loop is contractually allowed to touch:
``boundary``, ``principle``, and ``applicability``. The
mapping is the same one that the Interpretation Policy
(``backend/caseos/knowledge/feedback/interpretation/policy.py``)
uses in V1; the Evolution Governance Gate re-asserts the
allow-list as a defence-in-depth check.

Forbidden change types V1:

    identity_update             (G2 -- Identity Protection)
    delete_knowledge            (general -- not in allow list)
    rewrite_evidence            (G3 -- Evidence Protection)
    delete_evidence             (G3 -- Evidence Protection)
    modify_trust                (G4 -- Intelligence Isolation)
    modify_decision_rule        (G4 -- Intelligence Isolation)
    modify_retrieval_priority   (G4 -- Intelligence Isolation)

The forbidden set is broken into three sub-groups so the
Governance Gate can report a precise ``rule_id`` (``G2``,
``G3``, ``G4``) instead of a generic ``G1``.

Architecture boundary (Sprint 22.4-B spec Task 4):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.objects
        * caseos.knowledge.governance
        * caseos.knowledge.feedback
        * stdlib
"""
from __future__ import annotations

from typing import FrozenSet


# ---------------------------------------------------------------------------
# Allowed change types (positive allow-list)
# ---------------------------------------------------------------------------

ALLOWED_CHANGE_TYPES: FrozenSet[str] = frozenset({
    "boundary_update",
    "principle_update",
    "applicability_update",
})


# ---------------------------------------------------------------------------
# Forbidden change types (named rejection groups)
# ---------------------------------------------------------------------------

# G2 -- Identity Protection: identity is the KO's stable anchor.
G2_FORBIDDEN_CHANGE_TYPES: FrozenSet[str] = frozenset({
    "identity_update",
})

# G3 -- Evidence Protection: evidence is read-only for evolution.
G3_FORBIDDEN_CHANGE_TYPES: FrozenSet[str] = frozenset({
    "rewrite_evidence",
    "delete_evidence",
})

# G4 -- Intelligence Isolation: evolution never touches engines.
G4_FORBIDDEN_CHANGE_TYPES: FrozenSet[str] = frozenset({
    "modify_trust",
    "modify_decision_rule",
    "modify_retrieval_priority",
})

# Full forbidden set (union of G2/G3/G4 plus the general ones).
# ``delete_knowledge`` is a general "no" that is caught by G1
# (not in ALLOWED_CHANGE_TYPES); it is included here for
# documentation and for any future rule that wants to enumerate
# the full blacklist.
FORBIDDEN_CHANGE_TYPES: FrozenSet[str] = frozenset(
    G2_FORBIDDEN_CHANGE_TYPES
    | G3_FORBIDDEN_CHANGE_TYPES
    | G4_FORBIDDEN_CHANGE_TYPES
    | frozenset({"delete_knowledge"})
)


class EvolutionChangePolicy:
    """Stateless change policy. Pure functions over change_type."""

    @staticmethod
    def is_allowed(change_type: str) -> bool:
        """Return True iff the change_type is in the V1 allow-list."""
        return change_type in ALLOWED_CHANGE_TYPES

    @staticmethod
    def is_forbidden(change_type: str) -> bool:
        """Return True iff the change_type is in any forbidden set."""
        return change_type in FORBIDDEN_CHANGE_TYPES

    @staticmethod
    def is_g2_forbidden(change_type: str) -> bool:
        return change_type in G2_FORBIDDEN_CHANGE_TYPES

    @staticmethod
    def is_g3_forbidden(change_type: str) -> bool:
        return change_type in G3_FORBIDDEN_CHANGE_TYPES

    @staticmethod
    def is_g4_forbidden(change_type: str) -> bool:
        return change_type in G4_FORBIDDEN_CHANGE_TYPES


__all__ = [
    "ALLOWED_CHANGE_TYPES",
    "FORBIDDEN_CHANGE_TYPES",
    "G2_FORBIDDEN_CHANGE_TYPES",
    "G3_FORBIDDEN_CHANGE_TYPES",
    "G4_FORBIDDEN_CHANGE_TYPES",
    "EvolutionChangePolicy",
]
