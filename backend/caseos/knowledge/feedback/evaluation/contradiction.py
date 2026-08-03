"""Feedback Contradiction Result Object (Sprint 22.2-B.1, ADR-018 Section 4.5).

A ``ContradictionResult`` is the structured output of the contradiction
layer. It is a piece of evidence *about* a feedback / Knowledge Object
pair; it is **not** a Knowledge Object, a Decision rule, or a Trust
value.

This module defines the data shape only. The analyzer that *produces*
instances of ``ContradictionResult`` is intentionally out of scope for
Sprint 22.2-B.1 and will be added in a later sub-sprint.

Architecture boundary (Sprint 22.2-B.1 spec section 4):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.feedback (parent module)

The result is **immutable**: once produced by the (future) analyzer,
its fields are not mutated. Downstream layers may construct a new
``ContradictionResult`` if they need to amend a verdict; they never
edit one in place. This mirrors the append-only rule of ADR-018
Section 10 rule 4 ("the Loop is append-only").
"""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class ContradictionResult:
    """A single contradiction analysis verdict.

    Required fields (Sprint 22.2-B.1 spec section 1):

        feedback_id            identifier of the feedback being evaluated
        target_identity        identity of the Knowledge Object targeted
        has_conflict           True when the analyzer detected a potential
                               conflict between feedback and KO
        conflict_type          one of the taxonomy values (e.g.
                               "contradicts_boundary", "no_conflict", ...)
        matched_field          the KO field the contradiction points at
                               (empty string when has_conflict is False)
        explanation            human-readable description of the verdict
        requires_human_review  True when a human reviewer must look at
                               the result before any downstream action

    The dataclass is **frozen**: every field is part of the public
    record and cannot be reassigned. The ``to_dict`` helper produces
    a JSON-safe serialisation.
    """

    feedback_id: str
    target_identity: str
    has_conflict: bool
    conflict_type: str
    matched_field: str
    explanation: str
    requires_human_review: bool
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        """Serialise. The fields are primitives / strings, so
        ``asdict`` is JSON-safe as-is."""
        return asdict(self)


__all__ = ["ContradictionResult"]
