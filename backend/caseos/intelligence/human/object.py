"""HumanContext -- Sprint 21 (ADR-013 Section 2).

`HumanContext` is the structured output of the Human Understanding
stage. It is a snapshot of *what CaseOS understood about the human
behind the project* given only the structured inputs the user
supplied (the project JSON, plus future explicit user signals).

Architecture principle (ADR-013 Section 2):

    Human Understanding does NOT decide.
    Human Context influences retrieval / decision / recommendation.
    Decision remains the authority.

Hard rules (Sprint 21 spec section "NOT INCLUDED"):

    * No LLM calls       -- we never call a language model.
    * No NLP model       -- we never call a classifier.
    * No chatbot         -- we never have a conversation.
    * No vision / DB / API -- structured input only.

This means HumanContext is NOT a confidence-scoring AI model. It
is a deliberate, explicit envelope of structured fields. When the
user did not supply a piece of information, the corresponding field
holds the `UNKNOWN` sentinel -- it does NOT become `None`,
empty string, or a guessed default. This is the "Anti-Hallucination
Principle" applied to human understanding.

Required fields (Sprint 21 spec section 2):

    user_goal            what the user wants to achieve
    business_context     who they are / what kind of project this is
    emotional_preference how they want the space to feel
    budget_context       budget posture (low / medium / high / ...)
    constraints          hard constraints (cannot demolish, etc.)
    success_definition   what success looks like to the user

Optional fields (Sprint 21 spec section 2):

    risk_tolerance       how much uncertainty the user will accept
    decision_priority    speed / cost / quality / safety / ...
    unknowns             the explicit list of fields we don't know
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional


# Explicit sentinel. Using a string (rather than None) means
# `ctx.human_context["user_goal"] == ""` and
# `ctx.human_context["user_goal"] is UNKNOWN` remain distinguishable
# downstream. Downstream rules (decision, retrieval) treat UNKNOWN
# as "no signal" without crashing or inventing.
UNKNOWN = "__UNKNOWN__"


def _is_unknown(value: Any) -> bool:
    return value is None or value == "" or value == UNKNOWN


@dataclass
class HumanContext:
    """Structured Human Understanding output.

    The object is a dataclass (not a dict) so type checkers can
    help, but `to_dict()` and `from_dict()` preserve the
    JSON-serialisable shape that the existing pipeline stages
    already consume via `ctx.human_context[...]`.
    """

    # Required fields (Sprint 21 spec section 2).
    user_goal: str = UNKNOWN
    business_context: str = UNKNOWN
    emotional_preference: str = UNKNOWN
    budget_context: str = UNKNOWN
    constraints: list[str] = field(default_factory=list)
    success_definition: str = UNKNOWN

    # Optional fields.
    risk_tolerance: str = UNKNOWN
    decision_priority: str = UNKNOWN

    # Runtime metadata.
    schema_version: str = "human_context_v1"
    project_id: str = ""

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialise. `UNKNOWN` values stay as the literal sentinel
        so downstream stages can inspect them. The dynamic
        `unknowns` list is also embedded so downstream consumers
        (renderer, retrieval) can read it without re-deriving."""
        out = asdict(self)
        out["unknowns"] = self.unknowns()
        return out

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HumanContext":
        """Hydrate from a dict. Unknown keys are dropped silently."""
        known = {f for f in cls.__dataclass_fields__}
        base = {k: v for k, v in data.items() if k in known}
        return cls(**base)

    # ------------------------------------------------------------------
    # Convenience accessors used by the renderer + tests
    # ------------------------------------------------------------------

    def unknowns(self) -> list[str]:
        """Return the list of fields the user did not supply.

        The field name is added when the value is empty / None /
        UNKNOWN. `constraints` is excluded so that an empty
        constraints list is NOT treated as missing.
        """
        out: list[str] = []
        for name in (
            "user_goal",
            "business_context",
            "emotional_preference",
            "budget_context",
            "success_definition",
            "risk_tolerance",
            "decision_priority",
        ):
            if _is_unknown(getattr(self, name, UNKNOWN)):
                out.append(name)
        return out

    def is_unknown(self, field_name: str) -> bool:
        value = getattr(self, field_name, UNKNOWN)
        return _is_unknown(value)

    def summary(self) -> dict[str, Any]:
        """A small JSON-safe summary used by the report + renderer."""
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "user_goal": self.user_goal,
            "business_context": self.business_context,
            "emotional_preference": self.emotional_preference,
            "budget_context": self.budget_context,
            "constraints": list(self.constraints),
            "success_definition": self.success_definition,
            "risk_tolerance": self.risk_tolerance,
            "decision_priority": self.decision_priority,
            "unknowns": self.unknowns(),
        }


__all__ = ["HumanContext", "UNKNOWN", "_is_unknown"]
