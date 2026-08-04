"""Evolution Governance Gate V1 (Sprint 22.4-B, ADR-020).

The Governance Gate is the **independent validation layer**
between the Evolution Transaction and any future Knowledge
Object write-back. It is a pure function over an
``EvolutionTransaction`` (and optionally a ``ChangeIntent`` and
a Knowledge snapshot). It does NOT mutate any external state.

The Gate answers one question:

    "Is this change allowed to be considered for evolution?"

It does NOT answer:

    "Should this change be applied?"
    "What does the new KO look like?"

Those are downstream concerns, gated on ADR-020 Rules 1-5 and
on a concrete future Sprint 22.4.x runtime.

Validation rules (Sprint 22.4-B spec Task 3):

    G1  Change Type Allowed
            change_type must be in
            {boundary_update, principle_update,
             applicability_update}. Otherwise reject.
    G2  Identity Protection
            ``identity_update`` is rejected. Identity is
            the KO's stable anchor.
    G3  Evidence Protection
            ``rewrite_evidence`` and ``delete_evidence`` are
            rejected. Evidence is read-only.
    G4  Intelligence Isolation
            ``modify_trust``, ``modify_decision_rule``, and
            ``modify_retrieval_priority`` are rejected.
            Evolution never touches engines.
    G5  Human Approval Required
            ``reviewer`` must be a non-empty string.
    G6  Snapshot Required
            ``before_snapshot`` must be a non-empty dict.

Rule order: G2, G3, G4 are checked first (named rejections
that deserve a precise rule_id). Then G1 (the generic
allow-list). Then G5 and G6 (independent safety checks). The
first rule that fails determines the result; later rules are
not evaluated.

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

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .contracts.change_type import EvolutionChangeType
from .object import EvolutionTransaction
from .policy import (
    ALLOWED_CHANGE_TYPES,
    EvolutionChangePolicy,
    G2_FORBIDDEN_CHANGE_TYPES,
    G3_FORBIDDEN_CHANGE_TYPES,
    G4_FORBIDDEN_CHANGE_TYPES,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class GovernanceResult:
    """The outcome of a governance check.

    Attributes:
        approved: True iff every rule passed.
        rule_id: The first rule that failed (e.g. ``"G1"``).
            Empty string when ``approved``.
        reason: Human-readable reason for the decision. Empty
            string when ``approved``.
        checked_at: ISO timestamp (datetime). Defaults to
            ``datetime.now(timezone.utc)``.
    """

    approved: bool
    rule_id: str
    reason: str
    checked_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        out = asdict(self)
        ts = out.get("checked_at")
        if isinstance(ts, datetime):
            out["checked_at"] = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        return out


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_nonempty_dict(value: Any) -> bool:
    return isinstance(value, dict) and bool(value)


class EvolutionGovernanceGate:
    """Stateless governance gate. ``govern`` is a pure function."""

    def govern(
        self,
        transaction: Optional[EvolutionTransaction],
        change_intent: Any = None,
        knowledge_snapshot: Any = None,
    ) -> GovernanceResult:
        """Return a ``GovernanceResult`` for the given inputs.

        Args:
            transaction: the EvolutionTransaction to validate.
            change_intent: optional ChangeIntent. When provided,
                its ``change_type`` is cross-checked against the
                transaction's ``change_type``; a mismatch is
                treated as a G1 failure.
            knowledge_snapshot: optional external Knowledge
                snapshot. In V1 this is accepted for integration
                contract documentation but is not used to
                compute the verdict. A future Sprint 22.4.x
                governance rule may consult it.

        Returns:
            A ``GovernanceResult`` whose ``approved`` is True
            iff every rule passed.
        """
        if transaction is None:
            return GovernanceResult(
                approved=False,
                rule_id="G0",
                reason="transaction is None",
            )

        # Sprint 22.4-I: ``change_type`` is now an
        # ``EvolutionChangeType`` enum. We normalise to the
        # bare string for the G2/G3/G4 frozenset checks
        # (those sets intentionally remain string-literals),
        # and we check the enum against ``ALLOWED_CHANGE_TYPES``
        # which is a frozenset of enum members.
        raw_change_type = getattr(transaction, "change_type", None) or ""
        change_type_str = (
            raw_change_type.value
            if isinstance(raw_change_type, EvolutionChangeType)
            else str(raw_change_type)
        )

        # Cross-check ChangeIntent when provided. Both sides
        # are normalised to string for comparison.
        if change_intent is not None:
            ci_raw = getattr(change_intent, "change_type", None)
            ci_str = (
                ci_raw.value
                if isinstance(ci_raw, EvolutionChangeType)
                else str(ci_raw) if ci_raw is not None else None
            )
            if ci_str is not None and ci_str != change_type_str:
                return GovernanceResult(
                    approved=False,
                    rule_id="G1",
                    reason=(
                        "change_type mismatch: transaction="
                        + change_type_str
                        + ", change_intent="
                        + ci_str
                    ),
                )

        # G2 -- Identity Protection (most specific first)
        if change_type_str in G2_FORBIDDEN_CHANGE_TYPES:
            return GovernanceResult(
                approved=False,
                rule_id="G2",
                reason="identity_update forbidden; identity is the KO's stable anchor",
            )

        # G3 -- Evidence Protection
        if change_type_str in G3_FORBIDDEN_CHANGE_TYPES:
            return GovernanceResult(
                approved=False,
                rule_id="G3",
                reason="evidence rewrite/delete forbidden; evidence is read-only",
            )

        # G4 -- Intelligence Isolation
        if change_type_str in G4_FORBIDDEN_CHANGE_TYPES:
            return GovernanceResult(
                approved=False,
                rule_id="G4",
                reason=(
                    "intelligence engine mutation forbidden; "
                    "evolution only writes to KO fields"
                ),
            )

        # G1 -- Change Type Allowed (generic allow-list).
        # ALLOWED_CHANGE_TYPES is a frozenset of enum members.
        # If raw_change_type is not an enum member, fall back
        # to a string-coerced membership test.
        if isinstance(raw_change_type, EvolutionChangeType):
            allowed_ok = raw_change_type in ALLOWED_CHANGE_TYPES
        elif isinstance(raw_change_type, str):
            try:
                allowed_ok = (
                    EvolutionChangeType(raw_change_type)
                    in ALLOWED_CHANGE_TYPES
                )
            except ValueError:
                allowed_ok = False
        else:
            allowed_ok = False
        if not allowed_ok:
            return GovernanceResult(
                approved=False,
                rule_id="G1",
                reason=(
                    "change_type not in V1 allow-list: "
                    + repr(change_type_str)
                ),
            )

        # G5 -- Human Approval Required
        reviewer = getattr(transaction, "reviewer", None)
        if not _is_nonempty_str(reviewer):
            return GovernanceResult(
                approved=False,
                rule_id="G5",
                reason="reviewer is required (non-empty string)",
            )

        # G6 -- Snapshot Required
        before_snapshot = getattr(transaction, "before_snapshot", None)
        if not _is_nonempty_dict(before_snapshot):
            return GovernanceResult(
                approved=False,
                rule_id="G6",
                reason="before_snapshot is required (non-empty dict)",
            )

        return GovernanceResult(
            approved=True,
            rule_id="",
            reason="",
        )


__all__ = [
    "GovernanceResult",
    "EvolutionGovernanceGate",
]
