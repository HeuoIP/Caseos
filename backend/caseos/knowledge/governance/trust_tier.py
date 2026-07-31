"""Trust tier system aligned with ADR-016 Intelligence Trust Model.

Every Knowledge Object receives a TrustTier that describes the
quality of its source. Trust tier is orthogonal to the runtime
Confidence produced by the Trust Engine (Sprint 19.3):

  * Trust tier = property of the source (was the case real?
    was it reviewed by an expert?)
  * Confidence = property of a specific decision (how much
    evidence supported this recommendation?)

ADR-016 lists qualitative Source Reliability labels:
  - expert-verified
  - real-project-completed
  - theoretical-assumption

Sprint 20.6 collapses these into four TrustTiers:
  Tier_A: real_project_completed + expert_verified
  Tier_B: real_project_completed
  Tier_C: professional_case_reference
  Tier_D: conceptual_or_inspiration

A KO can declare a source_reliability list on itself. If absent,
assign_trust_tier() infers a default from the identity type so the
corpus stays governable before explicit labels exist.

Architecture boundary: this module never modifies a KO in place;
it only returns the assigned tier for downstream reporting."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class TrustTier(str, Enum):
    "Four-tier ladder aligned with ADR-016. Tier_A is the",
    "highest; Tier_D is the lowest. The string value is",
    "the canonical wire form (used in reports and JSON).",

    TIER_A = "Tier_A",
    TIER_B = "Tier_B",
    TIER_C = "Tier_C",
    TIER_D = "Tier_D",


# Source Reliability labels accepted on a KO (per ADR-016).
LABEL_EXPERT_VERIFIED = "expert-verified"
LABEL_REAL_COMPLETED = "real-project-completed"
LABEL_PROFESSIONAL_REF = "professional-case-reference"
LABEL_CONCEPTUAL = "conceptual"
LABEL_INSPIRATION = "inspiration"
LABEL_THEORETICAL = "theoretical-assumption"

# Default trust tier per identity type, used when a KO carries no
# explicit source_reliability labels. The defaults are conservative:
# a Golden Case is treated as a real completed project (Tier_B),
# abstracted patterns and failure records start at Tier_C, and a
# User Preference is treated as inspiration (Tier_D) until verified.
DEFAULT_TIER_BY_TYPE = {
    "GoldenCase": TrustTier.TIER_B,
    "DecisionPattern": TrustTier.TIER_C,
    "FailurePattern": TrustTier.TIER_C,
    "ExpertPrinciple": TrustTier.TIER_C,
    "UserPreference": TrustTier.TIER_D,
}


@dataclass
class TrustAssignment:
    "The result of assigning a TrustTier to a KO.",
    identity: str
    tier: TrustTier
    basis: str  # which source label(s) drove the assignment
    is_default: bool  # True when no source_reliability was declared

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity,
            "tier": self.tier.value,
            "basis": self.basis,
            "is_default": self.is_default,
        }


def _labels_from_ko(ko: dict) -> list[str]:
    "Extract the source_reliability labels declared on a KO.",
    raw = ko.get("source_reliability")
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw.strip()]
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    return []


def _type_from_identity(identity: str) -> str:
    "Identity strings follow the ADR-015 form",
    "IdentityType.name_vN. The type is the part before the",
    "first dot.",
    return identity.split(".", 1)[0] if "." in identity else ""


def assign_trust_tier(ko: dict) -> TrustAssignment:
    "Assign a TrustTier to a single Knowledge Object.",
    "",
    "The decision is deterministic:",
    "  1. real-project-completed AND expert-verified -> Tier_A.",
    "  2. real-project-completed (without expert-verified) -> Tier_B.",
    "  3. professional-case-reference -> Tier_C.",
    "  4. inspiration / conceptual / theoretical -> Tier_D.",
    "  5. Otherwise fall back to the identity-type default",
    "     (Tier_B for GoldenCase, Tier_C for patterns,",
    "     Tier_D for UserPreference).",
    identity = str(ko.get("identity") or "<unknown>")
    labels = _labels_from_ko(ko)
    has_real = LABEL_REAL_COMPLETED in labels
    has_expert = LABEL_EXPERT_VERIFIED in labels
    has_ref = LABEL_PROFESSIONAL_REF in labels
    has_conceptual = any(
        l in (LABEL_CONCEPTUAL, LABEL_INSPIRATION, LABEL_THEORETICAL)
        for l in labels
    )
    is_default = not labels

    if has_real and has_expert:
        return TrustAssignment(
            identity, TrustTier.TIER_A,
            "real-project-completed + expert-verified",
            False,
        )
    if has_real:
        return TrustAssignment(
            identity, TrustTier.TIER_B,
            "real-project-completed",
            False,
        )
    if has_ref:
        return TrustAssignment(
            identity, TrustTier.TIER_C,
            "professional-case-reference",
            False,
        )
    if has_conceptual:
        return TrustAssignment(
            identity, TrustTier.TIER_D,
            "conceptual/inspiration/theoretical",
            False,
        )

    itype = _type_from_identity(identity)
    default = DEFAULT_TIER_BY_TYPE.get(itype, TrustTier.TIER_D)
    return TrustAssignment(
        identity, default,
        "identity-type default (" + itype + ")",
        True,
    )


def assign_tiers(kos: list) -> list[TrustAssignment]:
    "Assign trust tiers to a list of KOs. Order preserved.",
    return [assign_trust_tier(ko) for ko in kos]


def distribution(assignments: list[TrustAssignment]) -> dict[str, int]:
    "How many KOs landed in each tier. Used by the report.",
    out = {tier.value: 0 for tier in TrustTier}
    for a in assignments:
        out[a.tier.value] += 1
    return out


__all__ = [
    "TrustTier",
    "TrustAssignment",
    "assign_trust_tier",
    "assign_tiers",
    "distribution",
]
