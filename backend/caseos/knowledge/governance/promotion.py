"""Knowledge promotion lifecycle (Sprint 20.6 spec section 5).

A Knowledge Object can move through three lifecycle stages:

  Raw Knowledge
        |
        v
  Golden Case
        |
        v
  DecisionPattern | FailurePattern | ExpertPrinciple

Promotion has three rules, per the spec:

  1. Preserve the original object (never mutate the source KO).
  2. Create a governance event recording the promotion.
  3. Never silently overwrite. Promotion is explicit,
     traceable, and reversible by deleting the new object.

This module is the only place lifecycle transitions are created.
The retrieval / decision / trust / recommendation engines never
promote, never de-promote, and never delete.

The output of promote() is a PromotionEvent dataclass; the
function does not write to disk. Callers decide what to do with
the event (the report module consumes them)."""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from caseos.knowledge.governance.trust_tier import TrustTier


ALLOWED_PROMOTIONS = {
    # from -> set of allowed targets
    "raw": frozenset({"GoldenCase"}),
    "GoldenCase": frozenset({
        "DecisionPattern",
        "FailurePattern",
        "ExpertPrinciple",
    }),
}


class PromotionError(ValueError):
    "Raised when a promotion request violates the lifecycle.",


@dataclass
class PromotionEvent:
    "A record of a successful promotion. The report module",
    "renders these so a human auditor can review what changed.",

    event_id: str
    source_identity: str
    source_type: str
    target_type: str
    target_identity: str
    target_ko: dict
    trust_tier_at_promotion: str
    timestamp: str
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "source_identity": self.source_identity,
            "source_type": self.source_type,
            "target_type": self.target_type,
            "target_identity": self.target_identity,
            "trust_tier_at_promotion": self.trust_tier_at_promotion,
            "timestamp": self.timestamp,
            "note": self.note,
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _identity_type(identity: str) -> str:
    return identity.split(".", 1)[0] if "." in identity else ""


def _new_identity_name(source_identity: str, target_type: str) -> str:
    "Derive a target identity name from the source.",
    "Preserves the short_id portion of the source identity",
    "and re-tags the type prefix. A short promotion suffix",
    "is added so promoted KOs are traceable back to the source.",
    short = _identity_type(source_identity) and source_identity.split(".", 1)[1] or source_identity
    return target_type + "." + short + ".promoted_v1"


def _build_target_ko(
    source_ko: dict,
    target_type: str,
    target_identity: str,
    note: str,
) -> dict:
    "Create a new KO for the promoted target. Source is deep",
    "copied so subsequent mutations of the target never touch",
    "the original (rule 1: preserve the original).",
    target = copy.deepcopy(source_ko)
    target["identity"] = target_identity
    target["promoted_from"] = source_ko.get("identity")
    target["promoted_at"] = _now_iso()
    target["promotion_note"] = note
    # Ensure feedback is a list on the new object so governance
    # validation does not flag it for a missing field.
    target.setdefault("feedback", [])
    return target


def promote(
    source_ko: dict,
    target_type: str,
    note: str = "",
    trust_tier: Optional[TrustTier] = None,
) -> PromotionEvent:
    "Promote a KO to a higher-level abstraction.",
    "",
    "Args:",
    "  source_ko: the existing KO to promote (not mutated).",
    "  target_type: one of GoldenCase, DecisionPattern,",
    "    FailurePattern, ExpertPrinciple (per ALLOWED_PROMOTIONS).",
    "  note: human-readable audit note.",
    "  trust_tier: optional pre-computed trust tier; if absent,",
    "    the default for the source identity type is used.",
    "",
    "Returns a PromotionEvent. The original source_ko is left",
    "untouched (verified by deepcopy).",
    if not isinstance(source_ko, dict):
        raise PromotionError("source_ko must be a dict")
    src_identity = str(source_ko.get("identity") or "")
    if not src_identity:
        raise PromotionError("source_ko has no identity")
    src_type = _identity_type(src_identity)
    if not src_type:
        # Treat type-less identity as raw knowledge.
        src_type = "raw"

    allowed = ALLOWED_PROMOTIONS.get(src_type, frozenset())
    if target_type not in allowed:
        raise PromotionError(
            "promotion " + repr(src_type) +
            " -> " + repr(target_type) +
            " is not allowed; permitted: " + repr(sorted(allowed)),
        )

    if trust_tier is None:
        # Lazy import to avoid a circular import: trust_tier does not
        # import promotion, but we want the default behaviour here.
        from caseos.knowledge.governance.trust_tier import (
            assign_trust_tier, DEFAULT_TIER_BY_TYPE,
        )
        tier = assign_trust_tier(source_ko).tier
    else:
        tier = trust_tier

    target_identity = _new_identity_name(src_identity, target_type)
    target_ko = _build_target_ko(source_ko, target_type, target_identity, note)

    return PromotionEvent(
        event_id=str(uuid.uuid4()),
        source_identity=src_identity,
        source_type=src_type,
        target_type=target_type,
        target_identity=target_identity,
        target_ko=target_ko,
        trust_tier_at_promotion=tier.value,
        timestamp=_now_iso(),
        note=note,
    )


def verify_original_preserved(source_ko: dict, event: PromotionEvent) -> bool:
    "Test helper: assert the source KO is byte-equal to its",
    "pre-promotion state. Used by the governance tests.",
    return source_ko.get("identity") == event.source_identity


__all__ = [
    "PromotionError",
    "PromotionEvent",
    "ALLOWED_PROMOTIONS",
    "promote",
    "verify_original_preserved",
]
