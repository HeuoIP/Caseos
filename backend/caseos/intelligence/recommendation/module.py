"""Recommendation Module -- Sprint 19.4 runtime implementation (ADR-017).

Status:
    Replaces the Sprint 19.1 placeholder with the first real
    customer-facing composition engine. Reuses the rule pattern
    established by Sprint 19.2 (Decision) and Sprint 19.3 (Trust):
    a small, inspectable `RecommendationEngine` plus a list of
    constraint rules that run AFTER the seven sections are composed.

Core Principle (ADR-017 Section 2 + Sprint 19.4 spec section 2):

    Decision Intelligence     -- decides WHAT
    Recommendation Engine     -- decides HOW TO COMMUNICATE

The engine NEVER:
    * rewrites the Decision Object
    * suggests equipment as a primary recommendation
    * drops Trust caveats to look "cleaner"

The engine ALWAYS:
    * renders the Decision\'s diagnosis verbatim
    * surfaces Trust evidence, confidence and caveats
    * produces all seven ADR-017 sections (or an honest "insufficient
      information" variant when the Decision Engine refused to
      commit)

The 7 sections emitted (ADR-017 Section 2.2):

    1. situation_understanding     -- mirror the user\'s stated problem
    2. problem_diagnosis           -- preserve the Decision\'s diagnosis
    3. strategic_direction         -- preserve the Decision\'s strategy
    4. experience_concept          -- translate strategy to experience
    5. implementation_direction    -- structural order, not equipment
    6. evidence                    -- render the Trust Object\'s evidence
    7. confidence_and_caveats      -- Trust confidence + uncertainty

Constraint rules (Sprint 19.4 spec section 5):

    RCM-01  No decision modification       (decision text preserved)
    RCM-02  No equipment list dumping      (forbidden vocabulary check)
    RCM-03  Trust must always appear       (evidence + confidence +
                                            caveats always present)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from caseos.brain.runtime import Stage
from caseos.brain.runtime.context import PipelineContext


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# ADR-017 Section 2.2 -- the seven sections in order.
SEVEN_SECTIONS: tuple[str, ...] = (
    "situation_understanding",
    "problem_diagnosis",
    "strategic_direction",
    "experience_concept",
    "implementation_direction",
    "evidence",
    "confidence_and_caveats",
)

# RCM-02 forbidden vocabulary: equipment-list anti-pattern.
# A real recommendation names the *problem* and *strategy*, never a
# catalogue of fixtures. We allow the words to appear ONLY inside the
# boundary (because the boundary explicitly forbids them) -- the
# section check below filters that out.
FORBIDDEN_EQUIPMENT = (
    "slide",
    "swing",
    "climbing frame",
    "trampoline",
    "rope net",
    "rope nets",
    "spiral slide",
    "seesaw",
)

# Canonical content type (ADR-017 Section 5.2).
DEFAULT_CONTENT_TYPE = "Strategic"

# Canonical audience variant for the kindergarten V1 demo.
DEFAULT_AUDIENCE = "kindergarten_owner"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has_rule_trace(decision: dict | None) -> bool:
    if not isinstance(decision, dict):
        return False
    trace = decision.get("_trace") or {}
    rid = trace.get("rule_id")
    return bool(rid) and rid != "None"


def _is_more_info_required(decision: dict | None) -> bool:
    """The Decision Engine refuses to commit when no V1 rule matches
    (ADR-014 Principle 5: "a Decision is allowed to refuse"). When
    that happens, the recommendation becomes an honest "tell the user
    we need more information" message -- not a finished
    recommendation. This is the RCM-04 path.
    """

    if not isinstance(decision, dict):
        return True
    if not _has_rule_trace(decision):
        return True
    decision_text = (decision.get("decision") or "").lower()
    return "more information required" in decision_text


def _join_list(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(str(v) for v in value if v)
    if value is None:
        return ""
    return str(value)


def _format_evidence(evidence: Any) -> str:
    """Render the Trust Object\'s `evidence` field as a single
    human-readable line. We do not rephrase or summarise the evidence;
    ADR-017 Section 2.2.6 says the list of sources stays visible.
    """

    if evidence is None or evidence == "":
        return "No explicit supporting evidence was provided."
    if isinstance(evidence, str):
        return evidence
    if isinstance(evidence, dict):
        parts: list[str] = []
        for k, v in evidence.items():
            parts.append(f"{k}: {v}")
        return " | ".join(parts) if parts else "No explicit supporting evidence was provided."
    if isinstance(evidence, list):
        return " | ".join(str(v) for v in evidence if v) or "No explicit supporting evidence was provided."
    return str(evidence)


# ---------------------------------------------------------------------------
# Section generators
# ---------------------------------------------------------------------------

def _section_situation(project, human_context: dict | None) -> str:
    """Mirror the project back to the user in their own language.

    ADR-017 Section 2.2.1: "We understand your situation. No jargon."
    """

    goal = (project.user_goal or "").strip()
    site = (project.site_description or "").strip()
    ptype = (project.project_type or "").strip() or "this project"

    if goal and site:
        return (
            f"You are working on a {ptype} where the goal is {goal}. "
            f"The current site condition you described: {site}."
        )
    if goal:
        return f"You are working on a {ptype} where the goal is {goal}."
    if site:
        return f"You are working on a {ptype} with the following site condition: {site}."
    return f"You are working on a {ptype}."


def _section_diagnosis(decision: dict) -> str:
    """Preserve the Decision Object\'s diagnosis verbatim.

    ADR-017 Section 2.2.2: "Diagnosis is never softened, never
    reworded, never substituted with a more flattering description."
    """

    diag = (decision.get("diagnosis") or "").strip()
    if diag:
        return diag
    return "The current signals do not yet allow a clear diagnosis."


def _section_strategy(decision: dict) -> str:
    """Surface the Decision\'s strategy + first move.

    ADR-017 Section 2.2.3: "The strategy is forward-looking: where
    the space should go, what the first move is, what to defer."
    """

    decision_text = (decision.get("decision") or "").strip()
    reasoning = (decision.get("reasoning") or "").strip()
    if not decision_text:
        return "No strategic direction is available yet."
    out = f"Strategic direction: {decision_text}."
    if reasoning:
        # Strip the rule-fired preamble so the customer reads a clean
        # strategy line, not an internal trace.
        cleaned = re.sub(
            r"^Rule\s+\S+\s+fired:\s*",
            "",
            reasoning,
        ).strip()
        if cleaned and cleaned.lower() != decision_text.lower():
            out += f" Reasoning: {cleaned}."
    return out


def _section_experience(decision: dict) -> str:
    """Translate the Decision into user-facing experience language.

    ADR-017 Section 2.2.4: NOT a list of equipment. A sentence the
    customer can read aloud.
    """

    if _is_more_info_required(decision):
        return (
            "We do not yet have enough information to describe a "
            "specific experience. Sharing more about the site and "
            "your goals will allow a more concrete direction."
        )

    decision_text = (decision.get("decision") or "").strip()
    if not decision_text:
        return "No experience direction is available yet."

    # Light translation: turn the strategy line into an "experience"
    # sentence. We deliberately keep the language generic; ADR-018
    # will add audience-aware vocabulary.
    return (
        f"Conceptually, the experience should embody: {decision_text}. "
        "Children and visitors should enter, explore, and stay, with a "
        "clear emotional anchor shaping the journey rather than a "
        "collection of disconnected activities."
    )


def _section_implementation(decision: dict) -> str:
    """Structural order-of-operations. Never a list of equipment.

    ADR-017 Section 2.2.5: "The order of operations: first which
    decision, next which kind of design, then which kind of
    validation."
    """

    if _is_more_info_required(decision):
        return (
            "Before any design investment, additional information is "
            "required. The next move is to clarify the site condition "
            "and the primary goal with the project owner."
        )

    boundary = (decision.get("boundary") or "").strip()
    decision_text = (decision.get("decision") or "").strip()

    parts: list[str] = []
    parts.append(
        "First, secure the strategic decision above as the project\'s "
        "guiding principle; everything that follows should be evaluated "
        "against it."
    )
    if decision_text:
        parts.append(
            "Next, organise the design around a central experience node "
            "and supporting activity paths -- not around isolated objects."
        )
    if boundary:
        parts.append(
            f"Throughout, hold the boundary: {boundary}."
        )
    parts.append(
        "Finally, validate the result against the original goal before "
        "committing further investment."
    )
    return " ".join(parts)


def _section_evidence(trust: dict | None) -> str:
    """Narrate the Trust Object\'s evidence and source reliability."""

    if not trust:
        return "No supporting evidence is available."
    evidence = trust.get("evidence")
    sources = trust.get("source_reliability") or []
    rendered = _format_evidence(evidence)
    if sources:
        source_line = "Source reliability: " + ", ".join(str(s) for s in sources) + "."
    else:
        source_line = "No source reliability information available."
    return f"{rendered} {source_line}"


def _section_confidence_caveats(trust: dict | None) -> dict[str, Any]:
    """Return the confidence_and_caveats sub-object.

    Shape is preserved for the markdown renderer; the renderer reads
    `confidence` and `caveats`.
    """

    if not trust:
        return {
            "confidence": "Unknown",
            "caveats": ["No Trust Object was available; recommend manual review."],
        }
    return {
        "confidence": trust.get("confidence") or "Unknown",
        "caveats": list(trust.get("uncertainty_handling") or trust.get("uncertainty") or []),
    }


# ---------------------------------------------------------------------------
# Rule base + three V1 constraint rules
# ---------------------------------------------------------------------------

@dataclass
class RecommendationRule:
    """A constraint rule that validates the composed recommendation.

    Mirrors the Decision Engine / Trust Engine Rule shape. The rule
    inspects the seven sections plus the source Decision + Trust
    Objects and contributes an entry to the `_trace` block. Rules
    that match set a flag in the trace; a rule that detects an
    anti-pattern should not corrupt the sections, only flag it.
    """

    id: str
    name: str

    def matches(self, sections: dict, decision: dict, trust: dict | None) -> bool:
        raise NotImplementedError


@dataclass
class RuleRCM01_NoDecisionModification(RecommendationRule):
    """Verify the Decision\'s diagnosis and strategy appear in the
    recommendation. If the engine has accidentally dropped or
    rewritten them, this rule fires and the trace is flagged.
    """

    id: str = "RCM-01"
    name: str = "Decision text must be preserved"

    def matches(self, sections: dict, decision: dict, trust: dict | None) -> bool:
        if _is_more_info_required(decision):
            return True  # trivial pass: no commitment to preserve
        diag = (decision.get("diagnosis") or "").strip()
        strat = (decision.get("decision") or "").strip()
        boundary = (decision.get("boundary") or "").strip()

        diagnosis_section = sections.get("problem_diagnosis", "")
        strategy_section = sections.get("strategic_direction", "")
        implementation_section = sections.get("implementation_direction", "")

        if diag and diag.lower() not in diagnosis_section.lower():
            return False
        if strat and strat.lower() not in strategy_section.lower():
            return False
        # The boundary should appear somewhere in implementation or
        # strategy. (We allow it to surface in either.)
        if boundary:
            blob = (strategy_section + " " + implementation_section).lower()
            if boundary.lower() not in blob:
                return False
        return True


@dataclass
class RuleRCM02_NoEquipmentList(RecommendationRule):
    """The experience_concept and implementation_direction sections
    must not be equipment lists.

    We do allow the boundary text to mention forbidden words (it
    explicitly forbids them), but those words must not be the
    *primary* recommendation.
    """

    id: str = "RCM-02"
    name: str = "No equipment list dumping"

    def matches(self, sections: dict, decision: dict, trust: dict | None) -> bool:
        # Get the boundary out of the way: it can mention forbidden
        # words because the boundary says "do not add X".
        boundary = (decision.get("boundary") or "").lower()

        combined = (
            sections.get("experience_concept", "")
            + " "
            + sections.get("implementation_direction", "")
        ).lower()

        for word in FORBIDDEN_EQUIPMENT:
            if word in combined and word not in boundary:
                return False
        return True


@dataclass
class RuleRCM03_TrustAlwaysPresent(RecommendationRule):
    """Evidence + confidence + caveats must always be present.

    Caveats may be an empty list (if the Trust Object emitted none),
    but the field itself must exist in the confidence_and_caveats
    block, and evidence + confidence must be non-empty strings.
    """

    id: str = "RCM-03"
    name: str = "Trust must always appear"

    def matches(self, sections: dict, decision: dict, trust: dict | None) -> bool:
        evidence = sections.get("evidence", "")
        cc = sections.get("confidence_and_caveats") or {}
        if not isinstance(evidence, str) or not evidence.strip():
            return False
        if not (cc.get("confidence") or "").strip():
            return False
        if "caveats" not in cc:
            return False
        return True


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class RecommendationEngine:
    """Composes the seven ADR-017 sections from Decision + Trust.

    The engine is intentionally tiny: a series of section
    generators (pure functions of the inputs) followed by a list
    of constraint rules that validate the composition. Future
    sprints can swap a section generator for an LLM call without
    touching the rule list.
    """

    def __init__(
        self,
        rules: list[RecommendationRule] | None = None,
        content_type: str = DEFAULT_CONTENT_TYPE,
        audience_variant: str = DEFAULT_AUDIENCE,
    ) -> None:
        self.rules = rules or [
            RuleRCM01_NoDecisionModification(),
            RuleRCM02_NoEquipmentList(),
            RuleRCM03_TrustAlwaysPresent(),
        ]
        self.content_type = content_type
        self.audience_variant = audience_variant

    def recommend(
        self,
        project,
        human_context: dict | None,
        decision: dict | None,
        trust: dict | None,
    ) -> dict[str, Any]:
        decision = decision or {}
        trust = trust or {}
        human_context = human_context or {}

        sections: dict[str, Any] = {
            "situation_understanding": _section_situation(project, human_context),
            "problem_diagnosis": _section_diagnosis(decision),
            "strategic_direction": _section_strategy(decision),
            "experience_concept": _section_experience(decision),
            "implementation_direction": _section_implementation(decision),
            "evidence": _section_evidence(trust),
            "confidence_and_caveats": _section_confidence_caveats(trust),
        }

        # Run constraint rules and collect trace flags.
        rule_results: list[dict[str, Any]] = []
        all_passed = True
        for rule in self.rules:
            ok = rule.matches(sections, decision, trust)
            if not ok:
                all_passed = False
            rule_results.append({
                "rule_id": rule.id,
                "rule_name": rule.name,
                "passed": bool(ok),
            })

        out: dict[str, Any] = {
            "schema_version": "recommendation_v1",
            "content_type": self.content_type,
            "audience_variant": self.audience_variant,
            "sections": sections,
            "constraint_results": rule_results,
            "all_constraints_passed": all_passed,
            "_trace": {
                "rule_order": [r.id for r in self.rules],
                "decision_rule_id": ((decision.get("_trace") or {}).get("rule_id")
                                      if isinstance(decision, dict) else None),
                "trust_rule_id": ((trust.get("_trace") or {}).get("rule_id")
                                   if isinstance(trust, dict) else None),
                "more_info_required": _is_more_info_required(decision),
            },
            "_engine_version": "recommendation_engine_v1",
        }
        return out


# ---------------------------------------------------------------------------
# Stage wrapper (Sprint 19.1 wire contract preserved)
# ---------------------------------------------------------------------------

class RecommendationModule(Stage):
    """Pipeline stage: `recommendation`.

    Same Stage contract as the Sprint 19.1 placeholder; the actual
    composition moved into `RecommendationEngine`.
    """

    name = "recommendation"

    def __init__(self, engine: RecommendationEngine | None = None) -> None:
        self.engine = engine or RecommendationEngine()

    def run(self, ctx: PipelineContext) -> PipelineContext:
        ctx.recommendation = self.engine.recommend(
            project=ctx.project,
            human_context=ctx.human_context,
            decision=ctx.decision_object,
            trust=ctx.trust_object,
        )
        return ctx


__all__ = [
    "RecommendationEngine",
    "RecommendationModule",
    "RecommendationRule",
    "RuleRCM01_NoDecisionModification",
    "RuleRCM02_NoEquipmentList",
    "RuleRCM03_TrustAlwaysPresent",
    "SEVEN_SECTIONS",
    "FORBIDDEN_EQUIPMENT",
]
