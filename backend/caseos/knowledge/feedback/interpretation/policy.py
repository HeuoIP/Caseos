"""Interpretation Policy V1 (Sprint 22.3.2, ADR-018 Section 3).

Maps an approved ``LearningProposal`` into a ``ChangeIntent`` that
is explicit, audit-friendly, and **never** auto-applies. The
policy is a pure function of its inputs; it does NOT mutate any
external state.

Architecture flow (Sprint 22.3.2 spec):

    LearningProposal (APPROVED + requires_human_review=True)
        |
        v
    InterpretationPolicy.interpret(...)
        |
        v
    ChangeIntent
        |
        v
    Human Approval (future: 22.4)
        |
        v
    Knowledge Evolution (future: 22.4, NOT in V1)

Supported mappings V1 (Sprint 22.3.2 spec Task 2):

    proposal_type              -> change_type          | target_field
    -----------------------------------------------------------
    boundary_update_candidate  -> boundary_update      | boundary
    principle_update_candidate -> principle_update     | principle

Any other proposal_type -> ``None``. The policy does NOT invent
new ``change_type`` values, does NOT touch unknown fields, and
does NOT modify the Knowledge Object.

Safety rules (Sprint 22.3.2 spec Task 3):

    Rule 1  proposal.requires_human_review must be True
    Rule 2  proposal.status must be APPROVED
    Rule 3  Knowledge Object is never modified (deepcopy-equal
            before and after interpret)
    Rule 4  Empty inputs return None -- missing target_identity,
            proposal_type, or reason short-circuits the policy
"""
from __future__ import annotations

import copy
import uuid
from typing import Any, Optional

from ..proposal import (
    PROPOSAL_TYPE_BOUNDARY,
    PROPOSAL_TYPE_PRINCIPLE,
)
from ...evolution.contracts.change_type import EvolutionChangeType
from .object import ChangeIntent, VALID_CHANGE_TYPES


# proposal_type -> (change_type, target_field, risk_level)
_MAPPING_V1: dict[str, tuple[EvolutionChangeType, str, str]] = {
    PROPOSAL_TYPE_BOUNDARY: (EvolutionChangeType.BOUNDARY_UPDATE, "boundary", "high"),
    PROPOSAL_TYPE_PRINCIPLE: (EvolutionChangeType.PRINCIPLE_UPDATE, "principle", "high"),
}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return "; ".join(str(x) for x in value)
    if isinstance(value, dict):
        return str(value)
    return str(value)


def _snapshot_field(knowledge_object: Any, field_name: str) -> Optional[str]:
    """Read a KO field by value. Returns ``None`` when absent.

    The function never mutates the input. It performs a shallow
    copy of any list / dict value before stringifying it.
    """
    if not isinstance(knowledge_object, dict):
        return None
    if field_name not in knowledge_object:
        return None
    raw = knowledge_object[field_name]
    if isinstance(raw, (list, tuple)):
        return "; ".join(str(x) for x in copy.copy(raw))
    if isinstance(raw, dict):
        return str(copy.copy(raw))
    return str(raw)


def _proposal_status_of(proposal: Any) -> str:
    return str(getattr(proposal, "status", "") or "")


def _proposal_proposal_type_of(proposal: Any) -> str:
    return str(getattr(proposal, "proposal_type", "") or "")


def _proposal_target_identity_of(proposal: Any) -> str:
    return str(getattr(proposal, "target_identity", "") or "")


def _proposal_reason_of(proposal: Any) -> str:
    return str(getattr(proposal, "reason", "") or "")


def _proposal_requires_human_review_of(proposal: Any) -> bool:
    return bool(getattr(proposal, "requires_human_review", False))


class InterpretationPolicy:
    """Stateless policy. ``interpret`` is a pure function of inputs."""

    def interpret(
        self,
        proposal: Any,
        knowledge_object: Any,
    ) -> Optional[ChangeIntent]:
        """Map an APPROVED proposal into a ChangeIntent.

        Returns ``None`` when any safety rule fails or when the
        proposal_type is not in the V1 mapping. The function
        never mutates the proposal or the Knowledge Object.
        """
        # Rule 1: requires_human_review must be True
        if not _proposal_requires_human_review_of(proposal):
            return None

        # Rule 2: status must be APPROVED
        if _proposal_status_of(proposal) != "APPROVED":
            return None

        # Rule 4: required fields must be present
        target_identity = _proposal_target_identity_of(proposal)
        proposal_type = _proposal_proposal_type_of(proposal)
        reason = _proposal_reason_of(proposal)
        if not target_identity or not proposal_type or not reason:
            return None

        # Mapping
        if proposal_type not in _MAPPING_V1:
            return None
        change_type, target_field, risk_level = _MAPPING_V1[proposal_type]
        if change_type not in VALID_CHANGE_TYPES:
            return None

        current_value = _snapshot_field(knowledge_object, target_field)
        # proposed_value is None in V1: the policy never invents
        # the future KO value. A future Knowledge Evolution sprint
        # (22.4) fills this in once a human approves the intent.
        proposed_value: Optional[str] = None

        return ChangeIntent(
            intent_id=str(uuid.uuid4()),
            proposal_id=str(getattr(proposal, "proposal_id", "") or ""),
            target_identity=target_identity,
            change_type=change_type,
            target_field=target_field,
            current_value=current_value,
            proposed_value=proposed_value,
            reason=reason,
            risk_level=risk_level,
            requires_human_review=True,
        )


__all__ = ["InterpretationPolicy"]
